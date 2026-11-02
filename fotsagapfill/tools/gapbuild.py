"""fotsagapfill builder v2 (0.2.0). Clones a donor FotSA variant into a new variant via JSON patches + cloned assets.
Usage: python -I work/gapbuild.py <species-id|all>   (specs in work/specs.py, per-species hooks in work/fixes.py).
STAGED output only: work/stage/ -> staging/fotsagapfill-0.2.0.zip. Never writes to the Mods folder.

Shape coordinate fact (measured with VsShapeCheck, 2026-10-31): child element from/to/rotationOrigin are RELATIVE to the
parent's `from` (moving a parent's `from` by dy moves its whole subtree by dy; moving `to` or rotationOrigin does not).
So scaling a subtree about a pivot P (parent frame) = element: v' = P + (v-P)*s for from/to/rotationOrigin;
descendants: every coordinate *= s. The pivot matters: scaling a thigh about its `from` (bottom corner) shortens the
whole leg chain and lifts the feet while the hip joint stays put; pivot 'ro'/'to' keeps the hip joint fixed.
"""
import zipfile, json, re, os, sys, glob, copy, colorsys, io, subprocess
import pyjson5
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = r'%APPDATA%\VintagestoryData\Mods'
STAGE = os.path.join(ROOT, 'work', 'stage')
TMPD = os.path.join(ROOT, 'work', '_tmp')
SUBDIRS = ('entities/', 'itemtypes/', 'blocktypes/', 'recipes/')
DLL = r'shape-harness\bin\Release\net10.0\VsShapeCheck.dll'
VERSION = '0.2.0'
EXTRA = {}        # stage path -> bytes (files in the fotsagapfill domain written by hooks)
EXTRA_PATCHES = []  # extra patch dicts
GROUND_LOG = []


def ptr(path):
    return '/' + '/'.join(str(p).replace('~', '~0').replace('/', '~1') for p in path)


def deepreplace(v, old, new):
    if isinstance(v, str):
        return v.replace(old, new)
    if isinstance(v, list):
        return [deepreplace(x, old, new) for x in v]
    if isinstance(v, dict):
        return {k.replace(old, new): deepreplace(x, old, new) for k, x in v.items()}
    return v


def deepmap(v, mapping):
    """replace substrings in string VALUES (not keys) per mapping dict."""
    if isinstance(v, str):
        for a, b in mapping.items():
            if a in v:
                v = v.replace(a, b)
        return v
    if isinstance(v, list):
        return [deepmap(x, mapping) for x in v]
    if isinstance(v, dict):
        return {k: deepmap(x, mapping) for k, x in v.items()}
    return v


class Donor:
    _cache = {}

    def __init__(self, zipname):
        self.zf = zipfile.ZipFile(os.path.join(MODS, zipname))
        mi = json.loads(self.zf.read('modinfo.json').decode('utf-8-sig'))
        self.modid = mi['modid']
        self.base = f'assets/{self.modid}/'
        self.orig = {}
        self.cur = {}
        self.changed = {}
        self.lang_add = {}
        self.assets = {}
        self.log = []

    @classmethod
    def get(cls, zipname):
        if zipname not in cls._cache:
            cls._cache[zipname] = Donor(zipname)
        return cls._cache[zipname]

    def parse(self, n):
        if n not in self.cur:
            o = pyjson5.loads(self.zf.read(n).decode('utf-8-sig'))
            self.orig[n] = copy.deepcopy(o)
            self.cur[n] = o
            self.changed[n] = set()
        return self.cur[n]

    def mutate(self, n, node, path, old, new):
        ch = self.changed[n]
        if isinstance(node, dict):
            items = list(node.items())
            out = []
            ins = False
            for k, v in items:
                if old in k:
                    nk = k.replace(old, new)
                    if nk not in node:
                        out.append((nk, deepreplace(v, old, new)))
                        ins = True
                else:
                    self.mutate(n, v, path + [k], old, new)
                out.append((k, v))
            if ins:
                node.clear()
                node.update(out)
                ch.add(tuple(path))
        elif isinstance(node, list):
            add = []
            for i, e in enumerate(node):
                if isinstance(e, str):
                    if old in e and e.replace(old, new) not in node:
                        add.append(e.replace(old, new))
                else:
                    self.mutate(n, e, path + [i], old, new)
            if add:
                node.extend(add)
                ch.add(tuple(path))

    def patches(self):
        res = []
        for n, ch in self.changed.items():
            keep = [p for p in ch if not any(len(q) < len(p) and p[:len(q)] == q for q in ch)]
            rel = n[len(self.base):]
            for p in sorted(keep, key=lambda t: tuple(map(str, t))):
                node = self.cur[n]
                for k in p:
                    node = node[k]
                res.append({'file': f'{self.modid}:{rel}', 'op': 'replace', 'path': ptr(p), 'value': node,
                            'dependsOn': [{'modid': self.modid}]})
        return res


class Ctx:
    """handle passed to per-species hooks (work/fixes.py)."""

    def __init__(self, d, spec):
        self.d, self.spec = d, spec
        self.new, self.old = spec['new_type'], spec['donor_type']

    def n(self, rel):
        return self.d.base + rel

    def doc(self, rel):
        return self.d.parse(self.n(rel))

    def mark(self, rel, *path):
        self.d.changed[self.n(rel)].add(tuple(path))

    def put(self, rel_asset, data):
        self.d.assets[self.n(rel_asset)] = data

    def lang(self, k, v):
        self.d.lang_add[k] = v

    def zread(self, zip_path):
        return self.d.zf.read(zip_path)

    def repoint(self, mapping, any_key=False):
        """in every parsed donor doc, for dict entries whose KEY contains the new type, replace substrings in string values."""
        cnt = 0
        for n, doc in self.d.cur.items():
            ch = self.d.changed[n]

            def w(node, path):
                nonlocal cnt
                if isinstance(node, dict):
                    for k, v in list(node.items()):
                        if any_key or self.new in k:
                            nv = deepmap(v, mapping)
                            if nv != v:
                                node[k] = nv
                                ch.add(tuple(path + [k]))
                                cnt += 1
                        else:
                            w(v, path + [k])
                elif isinstance(node, list):
                    for i, e in enumerate(node):
                        w(e, path + [i])
            w(doc, [])
        return cnt

    def set_first(self, rel, container_path, key, value):
        """put key FIRST in a ByType dict at container_path (first-match semantics), mark container changed."""
        doc = self.doc(rel)
        c = doc
        for k in container_path:
            c = c[k]
        items = [(key, value)] + [(k, v) for k, v in c.items() if k != key]
        c.clear()
        c.update(items)
        self.mark(rel, *container_path)


# ----------------------------------------------------------------- shape helpers
def each(elements, fn, parent=None):
    for e in elements:
        fn(e)
        each(e.get('children', []), fn)


def find_el(shape, name):
    res = []
    each(shape['elements'], lambda e: res.append(e) if e['name'] == name else None)
    return res[0] if res else None


def scale_children(c, s):
    sx, sy, sz = s
    for key in ('from', 'to', 'rotationOrigin'):
        if key in c:
            c[key] = [c[key][0] * sx, c[key][1] * sy, c[key][2] * sz]
    for cc in c.get('children', []):
        scale_children(cc, s)


def scale_subtree(el, s, pivot='from'):
    """scale element about a pivot (parent frame); descendants are parent-relative so their coords just multiply."""
    f, t = el['from'], el['to']
    ro = el.get('rotationOrigin', f)
    P = {'from': f, 'to': t, 'ro': ro, 'mid': [(f[i] + t[i]) / 2 for i in range(3)]}[pivot]
    P = list(P)
    for key in ('from', 'to', 'rotationOrigin'):
        if key in el:
            el[key] = [P[i] + (el[key][i] - P[i]) * s[i] for i in range(3)]
    for c in el.get('children', []):
        scale_children(c, s)


def descendants_of(e):
    out = []
    each(e.get('children', []), lambda x: out.append(x))
    return out


def remodel(shape, ops):
    """ops: ('scale', regex, (sx,sy,sz)[, anchors, pivot]) | ('move', regex, (dx,dy,dz)) | ('drop', regex)
    | ('rot', regex, (rx,ry,rz)) | ('addbox', parentRegex, element) | ('graft', parentRegex, dict)"""
    log = []
    for op in ops:
        kind, rx = op[0], op[1]
        hit = []
        each(shape['elements'], lambda e: hit.append(e) if re.fullmatch(rx, e['name']) else None)
        if kind == 'scale':
            ids = {id(h) for h in hit}
            # no double scaling: skip hits that sit under another hit of the same op
            dup = set()
            for h in hit:
                for d in descendants_of(h):
                    if id(d) in ids:
                        dup.add(id(d))
            hit = [h for h in hit if id(h) not in dup]
            anchors = op[3] if len(op) > 3 and op[3] else ''
            pivot = op[4] if len(op) > 4 else 'from'
            for e in hit:
                c0 = [(e['to'][i] + e['from'][i]) / 2 for i in range(3)]
                scale_subtree(e, op[2], pivot)
                for ax in anchors:   # re-centre the element box on these axes (children are parent-relative, they follow)
                    i = 'xyz'.index(ax)
                    sh = c0[i] - (e['to'][i] + e['from'][i]) / 2
                    for key in ('from', 'to', 'rotationOrigin'):
                        if key in e:
                            e[key][i] += sh
        elif kind == 'move':
            for e in hit:
                for key in ('from', 'to', 'rotationOrigin'):
                    if key in e:
                        e[key] = [e[key][i] + op[2][i] for i in range(3)]
        elif kind == 'rot':
            for e in hit:
                for ax, v in zip(('rotationX', 'rotationY', 'rotationZ'), op[2]):
                    e[ax] = e.get(ax, 0) + v
        elif kind == 'drop':
            def prune(e):
                e['children'] = [c for c in e.get('children', []) if not re.fullmatch(rx, c['name'])]
            each(shape['elements'], prune)
            shape['elements'] = [e for e in shape['elements'] if not re.fullmatch(rx, e['name'])]
        elif kind == 'addbox':
            for e in hit:
                e.setdefault('children', []).append(copy.deepcopy(op[2]))
        elif kind == 'graft':
            g = op[2]
            gz = zipfile.ZipFile(os.path.join(MODS, g['zip']))
            gs = pyjson5.loads(gz.read(g['path']).decode('utf-8-sig'))
            src = []
            each(gs['elements'], lambda e: src.append(e) if e['name'] == g['root'] else None)
            for e in hit:
                r = copy.deepcopy(src[0])
                k = g.get('scale', 1.0)
                dx = [g['from'][i] - r['from'][i] * k for i in range(3)]

                def fix(c, top):
                    for key in ('from', 'to', 'rotationOrigin'):
                        if key in c:
                            c[key] = [c[key][i] * k + (dx[i] if top else 0) for i in range(3)]
                    c['name'] = g['prefix'] + c['name']
                    for cc in c.get('children', []):
                        fix(cc, False)
                fix(r, True)
                if 'rotZ' in g:
                    r['rotationZ'] = g['rotZ']
                e.setdefault('children', []).append(r)
        log.append(f'{kind} {rx} x{len(hit)}')
    return log


# ------------------------------------------------------------ animation helpers
def anim_by_code(shape, code):
    for a in shape.get('animations', []):
        if a.get('code', '').lower() == code.lower():
            return a
    return None


def anim_scale_rot(shape, anim, el_rx, axis, factor, only_sign=None):
    """multiply rotation<axis> keys of elements matching regex in animation by factor."""
    a = anim_by_code(shape, anim)
    n = 0
    if not a:
        return 0
    for kf in a.get('keyframes', []):
        for en, v in kf.get('elements', {}).items():
            if re.fullmatch(el_rx, en) and ('rotation' + axis) in v:
                if only_sign is None or (v['rotation' + axis] * only_sign > 0):
                    v['rotation' + axis] *= factor
                    n += 1
    return n


def measure(shape, tag, anims=('idle',)):
    """lowest/highest world y, plus x/z extent over the given animations (blocks, model space, before entity size)."""
    import csv
    os.makedirs(TMPD, exist_ok=True)
    out = os.path.join(TMPD, 'out')
    os.makedirs(out, exist_ok=True)
    fp = os.path.join(TMPD, tag + '.json')
    json.dump(shape, open(fp, 'w'))
    codes = [a['code'] for a in shape.get('animations', []) if a.get('code', '').lower() in anims]
    cmd = ['dotnet', DLL, fp, '--out', out, '--frames', '2'] + (['--anim', ','.join(codes)] if codes else ['--static-only'])
    subprocess.run(cmd, capture_output=True, text=True)
    rows = list(csv.DictReader(open(os.path.join(out, tag + ('_frames.csv' if codes else '_static.csv')))))
    if not codes:
        rows = [r for r in rows if r['hasFaces'] == '1']
    f = lambda k: [float(r[k]) for r in rows]
    return dict(miny=min(f('miny')), maxy=max(f('maxy')), minx=min(f('minx')), maxx=max(f('maxx')), minz=min(f('minz')), maxz=max(f('maxz')))


def ground_shift(shape, tag, anims=('idle',)):
    """measure lowest y with the game's own transform code (VsShapeCheck), shift all roots so it is 0. Returns total shift (blocks)."""
    os.makedirs(TMPD, exist_ok=True)
    out = os.path.join(TMPD, 'out')
    os.makedirs(out, exist_ok=True)
    total = 0.0
    codes = [a['code'] for a in shape.get('animations', []) if a.get('code', '').lower() in anims]
    for _ in range(3):
        fp = os.path.join(TMPD, tag + '.json')
        json.dump(shape, open(fp, 'w'))
        cmd = ['dotnet', DLL, fp, '--out', out, '--frames', '2']
        if codes:
            cmd += ['--anim', ','.join(codes)]
        else:
            cmd += ['--static-only']
        subprocess.run(cmd, capture_output=True, text=True)
        import csv
        vals = []
        if codes:
            for r in csv.DictReader(open(os.path.join(out, tag + '_frames.csv'))):
                vals.append(float(r['miny']))
        else:
            for r in csv.DictReader(open(os.path.join(out, tag + '_static.csv'))):
                if r['hasFaces'] == '1':
                    vals.append(float(r['miny']))
        if not vals:
            break
        miny = min(vals)
        if abs(miny) < 0.004:
            break
        dy = -miny * 16
        for e in shape['elements']:
            for key in ('from', 'to', 'rotationOrigin'):
                if key in e:
                    e[key][1] += dy
        total += -miny
    GROUND_LOG.append((tag, round(total, 3)))
    return total


def recolor(png_bytes, steps):
    im = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    px = im.load()
    W, H = im.size

    def adj(r, g, b, st):
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        h = (h + st.get('dh', 0) / 360.0) % 1.0
        s = max(0, min(1, s * st.get('ms', 1) + st.get('as', 0)))
        v = max(0, min(1, v * st.get('mv', 1) + st.get('av', 0)))
        return tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(h, s, v))
    for st in steps:
        rect = st.get('rect', (0, 0, W, H))
        for y in range(max(0, rect[1]), min(H, rect[3])):
            for x in range(max(0, rect[0]), min(W, rect[2])):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                if 'only_hue' in st:
                    h = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)[0] * 360
                    lo, hi = st['only_hue']
                    if not (lo <= h <= hi):
                        continue
                px[x, y] = adj(r, g, b, st) + (a,)
    out = io.BytesIO()
    im.save(out, 'PNG')
    return out.getvalue(), (W, H)


# ------------------------------------------------------------- donor-pack overrides
def get_path(doc, path):
    for k in path:
        doc = doc[k]
    return doc


def apply_overrides(doc, new, spec):
    fields = spec.get('fields', {})
    climate = spec.get('climate')
    old = spec['donor_type']
    base_mean = []

    def fd(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if new in k and isinstance(v, dict) and 'climate' in v and k.replace(new, old) in n and 'climate' in n[k.replace(new, old)]:
                    c = n[k.replace(new, old)]['climate']
                    base_mean.append((c['minTemp'] + c['maxTemp']) / 2)
                fd(v)
        elif isinstance(n, list):
            for e in n:
                fd(e)
    fd(doc)
    delta = (((climate['minTemp'] + climate['maxTemp']) / 2) - base_mean[0]) if (climate and base_mean and 'minTemp' in climate) else 0

    def walk(node, parent_key):
        if isinstance(node, dict):
            for k, v in list(node.items()):
                if new in k and parent_key == 'TemperatureRangeByType' and isinstance(v, list) and delta:
                    a, b = v
                    node[k] = [a if a <= -40 else a + delta, b if b >= 60 else b + delta]
                elif new in k and parent_key in fields and not isinstance(v, dict):
                    f = fields[parent_key]
                    g = 'female' if 'female' in k else 'male' if 'male' in k else '*'
                    if g in f:
                        node[k] = f[g]
                    elif '*' in f:
                        node[k] = f['*']
                elif new in k and parent_key in fields and isinstance(v, dict):
                    f = fields[parent_key]
                    g = 'female' if 'female' in k else 'male' if 'male' in k else '*'
                    if g in f and isinstance(f[g], dict):
                        v.update(f[g])
                elif new in k and climate and isinstance(v, dict) and 'climate' in v:
                    v['climate'].update(climate)
                walk(node[k], k)
        elif isinstance(node, list):
            for e in node:
                walk(e, parent_key)
    walk(doc, '')


def inject(doc, new, spec, changed, path_root=()):
    for field, kv in spec.get('inject', {}).items():
        for holder_path in ((), ('client',)):
            h = doc
            ok = True
            for k in holder_path:
                if isinstance(h, dict) and k in h:
                    h = h[k]
                else:
                    ok = False
            if ok and isinstance(h, dict) and field in h and isinstance(h[field], dict):
                d = h[field]
                items = list(kv.items()) + [(k, v) for k, v in d.items() if k not in kv]
                d.clear()
                d.update(items)
                changed.add(tuple(path_root) + holder_path + (field,))
                break


def build(spec):
    d = Donor.get(spec['donor_zip'])
    old, new, dom = spec['donor_type'], spec['new_type'], d.modid
    rep = lambda s: s.replace(old, new)
    names = d.zf.namelist()
    touched = []
    for n in names:
        if not n.endswith('.json') or not n.startswith(d.base):
            continue
        rel = n[len(d.base):]
        if not rel.startswith(SUBDIRS) or old not in d.zf.read(n).decode('utf8', 'ignore'):
            continue
        doc = d.parse(n)
        before = json.dumps(doc, sort_keys=False)
        d.mutate(n, doc, [], old, new)
        if json.dumps(doc, sort_keys=False) != before:
            apply_overrides(doc, new, spec)
            if rel.startswith('entities/') and rel.endswith('-adult.json'):
                inject(doc, new, spec, d.changed[n])
                for side in ('client', 'server'):
                    for bi, b in enumerate(doc.get(side, {}).get('behaviors', [])):
                        if b.get('code') in spec.get('disable_behaviors', []):
                            ebt = b.get('enabledByType') or {'*': b.get('enabled', True)}
                            b['enabledByType'] = {**{f'*-{new}': False}, **ebt}
                            d.changed[n].add((side, 'behaviors', bi))
            touched.append(rel)
    # lang
    lang_add = d.lang_add
    lang = pyjson5.loads(d.zf.read(f'{d.base}lang/en.json').decode('utf-8-sig'))
    dn = next((v for k, v in lang.items() if re.fullmatch(rf'item-creature-.*-adult-female-{old}', k)), None)
    donor_name = re.sub(r'\s*\(.*\)$', '', dn) if dn else None
    nn = spec['common_name']
    pairs = []
    if donor_name:
        pairs.append((donor_name, nn))
    pairs += list(spec.get('names', {}).items())
    pk = next((v for k, v in lang.items() if k.startswith('game:prefixandcreature') and k.endswith(f'adult-female-{old}')), None)
    if pk:
        pk = re.sub(r'^(?:a|an) ', '', pk)
        pairs.append((pk, nn))
    pairs.sort(key=lambda t: -len(t[0]))
    for k, v in lang.items():
        if old in k:
            nv = v
            low = k.startswith('game:prefixandcreature')
            for src, dst in pairs:
                dd = dst.lower() if low else dst
                nv = re.sub(re.escape(src), lambda m: dd, nv, flags=re.I)
            for _, dst in pairs:
                dd = dst.lower() if low else dst
                nv = re.sub(r'(?<![A-Za-z])(?:a|an) (?=' + re.escape(dd) + ')', lambda m: ('an ' if dd[0].lower() in 'aeiou' else 'a '), nv, flags=re.I)
            lang_add[k.replace(old, new)] = nv
    # assets
    shape_ops = spec.get('shape_ops', [])
    baby_ops = spec.get('baby_ops', [])
    shape_fn = spec.get('shape_fn')
    logs = []

    def shape_pipeline(txt, kind, tag):
        shp = pyjson5.loads(txt)
        ops = shape_ops if kind == 'adult' else baby_ops
        if ops:
            logs.extend(f'shape {tag} {kind}: ' + x for x in remodel(shp, ops))
        if shape_fn:
            shape_fn(shp, kind)
        if spec.get('ground', False) and (kind == 'adult' or spec.get('ground_baby', True)) and (ops or shape_fn):
            sh = ground_shift(shp, f"{spec['id']}_{kind}")
            logs.append(f'ground {tag} {kind}: shift {sh:+.3f} blocks')
        return json.dumps(shp, indent=1)

    for n in names:
        if old in n and not n.endswith('/') and n.startswith(d.base) and not n.endswith(('.json',)) or (old in n and n.endswith('.json') and '/shapes/' in n):
            if n.endswith('/'):
                continue
            data = d.zf.read(n)
            nn_path = rep(n)
            if n.endswith('.json'):
                txt = data.decode('utf-8-sig')
                if '/shapes/entity/' in n and (n.endswith(('-adult.json', '/adult.json', '-baby.json', '/baby.json', f'/{old}.json'))):
                    kind = 'adult' if n.endswith(('-adult.json', '/adult.json', f'/{old}.json')) else 'baby'
                    txt = shape_pipeline(txt, kind, os.path.basename(n))
                data = rep(txt).encode()
            elif n.endswith('.png'):
                data, size = recolor(data, spec['recolor'])
                logs.append(f'texture {os.path.basename(n)} {size}')
            d.assets[nn_path] = data
    # extra cloned assets from the donor pack under a new name (e.g. another species' chick shape + texture)
    for ex in spec.get('extra_assets', []):
        data = d.zf.read(ex['src'])
        dst = ex['dst']
        if ex['kind'] == 'shape_baby' or ex['kind'] == 'shape_adult':
            kind = 'baby' if ex['kind'] == 'shape_baby' else 'adult'
            txt = shape_pipeline(data.decode('utf-8-sig'), kind, os.path.basename(dst))
            data = txt.encode()
        elif ex['kind'] == 'png':
            data, size = recolor(data, ex.get('recolor', spec['recolor']))
            logs.append(f'texture {os.path.basename(dst)} {size}')
        d.assets[dst] = data
    if spec.get('post'):
        spec['post'](Ctx(d, spec))
    d.log.append((spec['id'], touched, logs))
    return d


def d_touched_entities(d, s):
    res = set()
    for n, ch in d.changed.items():
        rel = n[len(d.base):]
        if rel.startswith('entities/') and ch and s['new_type'] in json.dumps(d.cur[n]):
            res.add(rel)
    return sorted(res)


def finish(donors, specs):
    import shutil
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    allp = []
    for d in donors:
        allp += d.patches()
        for p, b in d.assets.items():
            fp = os.path.join(STAGE, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, 'wb').write(b)
        lp = os.path.join(STAGE, d.base, 'lang', 'en.json')
        os.makedirs(os.path.dirname(lp), exist_ok=True)
        json.dump(d.lang_add, open(lp, 'w', encoding='utf8'), indent=1, ensure_ascii=False)
    for p, b in EXTRA.items():
        fp = os.path.join(STAGE, p)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        open(fp, 'wb').write(b if isinstance(b, bytes) else b.encode('utf8'))
    allp += EXTRA_PATCHES
    bio = {}
    for s in specs:
        if s.get('own_entity') or not s.get('donor_zip'):
            continue
        d = Donor.get(s['donor_zip'])
        for rel in d_touched_entities(d, s):
            bio.setdefault((d.modid, rel), {})[f"*-{s['new_type']}"] = {'biorealm': s['realm']}
    for (mod, rel), val in bio.items():
        allp.append({'file': f'{mod}:{rel}', 'op': 'addmerge', 'path': '/attributesByType', 'side': 'Server',
                     'value': val, 'dependsOn': [{'modid': 'biomes'}]})
    pp = os.path.join(STAGE, 'assets', 'fotsagapfill', 'patches', 'gapfill.json')
    os.makedirs(os.path.dirname(pp), exist_ok=True)
    json.dump(allp, open(pp, 'w'), indent=1)
    mi = {'type': 'content', 'modid': 'fotsagapfill', 'name': 'FotSA Gap-Fill (staged)', 'authors': ['Nick (generated)'],
          'description': 'Adds missing Stone Age fauna as variants of installed Fauna of the Stone Age packs (plus one own-domain entity derived from the vanilla bear). Requires the donor packs.',
          'version': VERSION, 'side': 'Universal'}
    json.dump(mi, open(os.path.join(STAGE, 'modinfo.json'), 'w'), indent=2)
    return len(allp)


def package(out):
    if os.path.exists(out):
        os.remove(out)
    z = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
    for r, _, fs in os.walk(STAGE):
        for f in fs:
            fp = os.path.join(r, f)
            z.write(fp, os.path.relpath(fp, STAGE).replace('\\', '/'))
    z.close()


def main():
    sys.path.insert(0, os.path.join(ROOT, 'work'))
    import specs
    want = sys.argv[1:] or ['all']
    sel = [s for s in specs.SPECS if 'all' in want or s['id'] in want]
    ds = []
    for s in sel:
        if s.get('own_entity'):
            s['own_entity'](s)      # builder function for species with no donor pack
        else:
            ds.append(build(s))
    ds = list({id(x): x for x in ds}.values())
    n = finish(ds, sel)
    os.makedirs(os.path.join(ROOT, 'staging'), exist_ok=True)
    package(os.path.join(ROOT, 'staging', f'fotsagapfill-{VERSION}.zip'))
    for d in ds:
        for sid, t, l in d.log:
            print(sid, 'files', len(t), '|', '; '.join(l)[:600])
    print('ground shifts:', GROUND_LOG)
    print('patches', n)


if __name__ == '__main__':
    sys.path.insert(0, os.path.join(ROOT, 'work'))
    import gapbuild
    gapbuild.main()
