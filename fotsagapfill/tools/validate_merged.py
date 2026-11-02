"""Validate work/merged/*.zip against the Mods originals and the staged addon. Prints summaries only.
Usage: python -I work/validate_merged.py"""
import os, re, sys, json, copy, zipfile, subprocess, shutil, collections
import pyjson5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'work'))
import specs
from merge_build import PACKS, MODS, parse, tokens, walk

MERGED = os.path.join(ROOT, 'work', 'merged')
EX = os.path.join(ROOT, 'work', 'merged_ex')
GAME = r'%APPDATA%\Vintagestory\assets'
DLL = r'shape-harness\bin\Release\net10.0\VsShapeCheck.dll'
A = zipfile.ZipFile(os.path.join(ROOT, 'staging', 'fotsagapfill-0.2.0.zip'))
PATCHES = json.loads(A.read('assets/fotsagapfill/patches/gapfill.json').decode('utf-8-sig'))
TYPES = collections.defaultdict(list)
for s in specs.SPECS:
    if s.get('donor_zip'):
        TYPES[s['donor_zip'][:-4]].append(s['new_type'])

# ---- global asset index (lowercased) ----
INDEX = set()
for f in os.listdir(MODS):
    p = os.path.join(MODS, f)
    if f.endswith('.zip') and not f.lower().startswith('fotsa-'):
        try:
            INDEX.update(n.lower() for n in zipfile.ZipFile(p).namelist())
        except Exception:
            pass
    elif f.lower().startswith('fotsa-') and f.endswith('.zip'):
        INDEX.update(n.lower() for n in zipfile.ZipFile(p).namelist())
for root, _, files in os.walk(GAME):
    for fn in files:
        rel = os.path.relpath(os.path.join(root, fn), GAME).replace('\\', '/')
        if '/' not in rel: continue
        d, rest = rel.split('/', 1)
        INDEX.add(('assets/%s/%s' % (d, rest)).lower()); INDEX.add(('assets/game/%s' % rest).lower())
print('asset index entries', len(INDEX))


def resolve(ref, dom, kinds, local):
    """kinds: list of (subdir, ext). returns 'ok' / 'game' (only via game fallback) / None"""
    d, p = (ref.split(':', 1) if ':' in ref else (dom, ref))
    for dd, tag in ((d, 'ok'), ('game', 'game')):
        for sub, ext in kinds:
            full = ('assets/%s/%s/%s%s' % (dd, sub, p, ext)).lower()
            if '*' in full or '{' in full:
                rx = re.compile('^' + re.escape(full).replace(r'\*', '.*').replace(r'\{', '{').replace(r'\}', '}') + '$')
                rx = re.compile('^' + re.sub(r'\\\{[^}]*\\\}', '.*', re.escape(full).replace(r'\*', '.*')) + '$')
                if any(rx.match(n) for n in local) or any(rx.match(n) for n in INDEX):
                    return tag
            else:
                if full in local or full in INDEX:
                    return tag
                if ext == '.ogg':
                    for k in ('1', '2'):
                        if ('assets/%s/%s/%s%s%s' % (dd, sub, p, k, ext)).lower() in local | INDEX:
                            return tag
        if d == 'game':
            break
    return None


def collect_refs(node, out, key=None, inside_sounds=False):
    if isinstance(node, dict):
        for k, v in node.items():
            collect_refs(v, out, k, inside_sounds or k.lower().startswith('sounds') or k.lower().endswith('sound'))
    elif isinstance(node, list):
        for v in node:
            collect_refs(v, out, key, inside_sounds)
    elif isinstance(node, str):
        if key in ('base', 'texture', 'shape') or (key and key.lower().startswith('shape')) or (isinstance(key, str) and key.lower().startswith('texture')):
            if key == 'texture' or 'texture' in str(key).lower():
                out.add(('tex', node))
            elif key == 'base':
                out.add(('base', node))
            else:
                out.add(('shape', node))
        elif inside_sounds and key not in ('type',):
            out.add(('snd', node))


tot = collections.Counter()
overall_ok = True
for dom, pack in PACKS.items():
    mz = zipfile.ZipFile(os.path.join(MERGED, pack + '.zip'))
    oz = zipfile.ZipFile(os.path.join(MODS, pack + '.zip'))
    bad = mz.testzip()
    mn, on = set(mz.namelist()), set(oz.namelist())
    added = sorted(mn - on)
    removed = sorted(on - mn)
    changed = sorted(n for n in mn & on if mz.read(n) != oz.read(n))
    types = TYPES[pack]
    # added files must belong to the new species
    stray_added = [n for n in added if not n.endswith('/') and not any(t in n for t in types)]
    allowed = re.compile(r'/(entities/|itemtypes/|recipes/|lang/en\.json$|patches/biomes\.json$)')
    stray_changed = [n for n in changed if not allowed.search(n)]
    # json parse of all changed/added json
    jfail = []
    for n in changed + added:
        if n.endswith('.json'):
            try:
                parse(mz.read(n))
            except Exception as e:
                jfail.append((n, str(e)[:80]))
    # independent patch check: value at each patch path equals patch value; nothing else changed
    ppatch = [op for op in PATCHES if op['file'].split(':')[0] == dom and not (op.get('side') == 'Server' and any(x.get('modid') == 'biomes' for x in op.get('dependsOn', [])))]
    docs_m, docs_o = {}, {}
    mism = 0
    for op in ppatch:
        fn = 'assets/%s/%s' % tuple(op['file'].split(':', 1))
        if fn not in docs_m:
            docs_m[fn] = parse(mz.read(fn))
            docs_o[fn] = parse(oz.read(fn))
        toks = tokens(op['path'])
        if walk(docs_m[fn], toks) != op['value']:
            mism += 1
        # restore original at path in merged copy
    restored_bad = 0
    for fn, dm in docs_m.items():
        d2 = copy.deepcopy(dm)
        d0 = docs_o[fn]
        for op in ppatch:
            if 'assets/%s/%s' % tuple(op['file'].split(':', 1)) != fn:
                continue
            t = tokens(op['path'])
            par2, par0 = walk(d2, t[:-1]), walk(d0, t[:-1])
            last = t[-1]
            if isinstance(par2, list):
                par2[int(last)] = copy.deepcopy(par0[int(last)])
            else:
                par2[last] = copy.deepcopy(par0[last])
        if d2 != d0:
            restored_bad += 1
    # biomes ops present and targets exist
    bl = parse(mz.read('assets/%s/patches/biomes.json' % dom))
    bo = [op for op in PATCHES if op['file'].split(':')[0] == dom and op.get('side') == 'Server' and any(x.get('modid') == 'biomes' for x in op.get('dependsOn', []))]
    biomes_present = all(op in bl for op in bo)
    biomes_targets = all(('assets/%s/%s' % tuple(op['file'].split(':', 1))) in mn for op in bo)
    # reference resolution from all strings in added/patched content
    local = {n.lower() for n in mn}
    refs = set()
    for op in ppatch:
        collect_refs(op['value'], refs)
    for n in added:
        if n.endswith('.json') and '/shapes/item/' not in n and '/shapes/entity/' not in n:
            collect_refs(parse(mz.read(n)), refs)
    unres, via_game = [], 0
    for kind, r in sorted(refs):
        if r.startswith('#') or '$' in r:
            continue
        kinds = {'tex': [('textures', '.png')], 'base': [('shapes', '.json'), ('textures', '.png')], 'shape': [('shapes', '.json')],
                 'snd': [('sounds', '.ogg')]}[kind]
        # only check refs relevant to the new species
        if kind != 'snd' and not any(t in r for t in types):
            if not r.startswith('fotsa'):
                continue
        res = resolve(r, dom, kinds, local)
        if kind == 'snd' and not any(t in r for t in types):
            res = resolve(r, dom, kinds, local)
        if res is None:
            unres.append((kind, r))
        elif res == 'game':
            via_game += 1
    # new-species shapes: internal texture refs (shape textures map) + item shapes
    shape_unres = []
    for n in added:
        if '/shapes/' in n and n.endswith('.json'):
            sh = parse(mz.read(n))
            for c, tp in (sh.get('textures') or {}).items():
                if isinstance(tp, str) and tp.startswith('#'):
                    continue
                if isinstance(tp, str) and resolve(tp, dom, [('textures', '.png')], local) is None:
                    shape_unres.append((n.split('/shapes/')[1][:60], c, tp))
    # lang: no fotsagapfill, no missing
    leak = [n for n in changed + added if n.endswith(('.json', '.png')) and n.endswith('.json') and b'fotsagapfill' in mz.read(n)]
    ok = (bad is None and not removed and not stray_added and not stray_changed and not jfail and mism == 0 and restored_bad == 0
          and biomes_present and biomes_targets and not unres and not shape_unres and not leak)
    overall_ok &= ok
    print('%s %s: testzip=%s entries %d->%d | added %d changed %d removed %d | stray add/chg %d/%d | json fail %d | patch value mism %d, off-path changes %d | biomes ops %d present=%s targets=%s | refs %d unresolved %d (via game fallback %d) | shape tex unres %d | fotsagapfill leak %d'
          % ('PASS' if ok else 'FAIL', pack, bad or 'OK', len(on), len(mn), len(added), len(changed), len(removed), len(stray_added), len(stray_changed), len(jfail),
             mism, restored_bad, len(bo), biomes_present, biomes_targets, len(refs), len(unres), via_game, len(shape_unres), len(leak)))
    for x in (stray_added[:3] + stray_changed[:3] + jfail[:3] + unres[:6] + shape_unres[:4] + leak[:3]):
        print('   >>', x)
    tot['added'] += len(added)
    tot['changed'] += len(changed)

# ---- standalone ----
sz = zipfile.ZipFile(os.path.join(MERGED, 'fotsagapfill-0.2.0.zip'))
print('standalone testzip', sz.testzip() or 'OK', len(sz.namelist()), 'files')
ent = parse(sz.read('assets/fotsagapfill/entities/animal/mammal/arctodus-adult.json'))
for n in sz.namelist():
    if n.endswith('.json'):
        parse(sz.read(n))
sl = {n.lower() for n in sz.namelist()}
refs = set()
collect_refs(ent, refs)
unres = []
for kind, r in sorted(refs):
    kinds = {'tex': [('textures', '.png')], 'base': [('shapes', '.json'), ('textures', '.png')], 'shape': [('shapes', '.json')], 'snd': [('sounds', '.ogg')]}[kind]
    if resolve(r, 'fotsagapfill', kinds, sl) is None:
        unres.append((kind, r))
print('standalone refs', len(refs), 'unresolved', unres[:8])
overall_ok &= not unres
print('OVERALL refs/diff validation:', 'PASS' if overall_ok else 'FAIL', dict(tot))

# ---- extract merged for shape checks ----
shutil.rmtree(EX, ignore_errors=True)
os.makedirs(EX)
for f in os.listdir(MERGED):
    if f.endswith('.zip'):
        zipfile.ZipFile(os.path.join(MERGED, f)).extractall(os.path.join(EX, 'all'))
nshape = errs = 0
for s in specs.SPECS:
    nt = s['new_type']
    base = os.path.join(EX, 'all', 'assets')
    for root, _, files in os.walk(base):
        rp = root.replace('\\', '/')
        if '/shapes/entity/' not in rp + '/':
            continue
        for fn in files:
            if fn.endswith('.json') and (nt in fn or nt in rp) and 'antlers' not in fn and (s.get('donor_zip') or 'arctodus' in rp):
                fp = os.path.join(root, fn)
                r = subprocess.run(['dotnet', DLL, fp, '--static-only', '--out', os.path.join(EX, '_o')], capture_output=True, text=True)
                m = re.search(r'findings: (\d+) error, (\d+) warn', r.stdout)
                e = int(m.group(1)) if m else -1
                nshape += 1
                if e != 0:
                    errs += 1
                    print('SHAPE FAIL', s['id'], fn, r.stdout[-200:])
print('VsShapeCheck static: shapes', nshape, 'with errors', errs)
