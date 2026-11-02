"""Merge staging/fotsagapfill-0.2.0.zip into the FotSA donor pack zips. Output: work/merged/<pack>.zip (+ standalone).
Usage: python -I work/merge_build.py   (reads Mods zips read-only, never writes to Mods)"""
import os, sys, json, copy, zipfile, collections, re
import pyjson5

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = r'%APPDATA%\VintagestoryData\Mods'
OUT = os.path.join(ROOT, 'work', 'merged')
ADDON = os.path.join(ROOT, 'staging', 'fotsagapfill-0.2.0.zip')
PACKS = {'dinornithidae': 'FotSA-Dinornithidae-v1.0.26', 'vombatidae': 'FotSA-Vombatidae-v0.4.8',
         'rhinocerotidae': 'FotSA-Rhinocerotidae-v1.0.29', 'viverridae': 'FotSA-Viverridae-v1.0.11',
         'meiolaniidae': 'FotSA-Meiolaniidae-v0.1.13', 'capreolinae': 'FotSA-Capreolinae-v2.0.20',
         'bovinae': 'FotSA-Bovinae-v0.3.6'}


def parse(b):
    t = b.decode('utf-8-sig')
    try:
        return pyjson5.loads(t)
    except Exception:
        return json.loads(t)


def tokens(path):
    return [p.replace('~1', '/').replace('~0', '~') for p in path.split('/')[1:]]


def walk(doc, toks):
    cur = doc
    for t in toks:
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur


def merge(dst, src):
    if isinstance(dst, dict) and isinstance(src, dict):
        for k, v in src.items():
            if k in dst:
                dst[k] = merge(dst[k], v)
            else:
                dst[k] = copy.deepcopy(v)
        return dst
    if isinstance(dst, list) and isinstance(src, list):
        dst.extend(copy.deepcopy(x) for x in src if x not in dst)
        return dst
    return copy.deepcopy(src)


def apply_op(doc, op, stats):
    toks = tokens(op['path'])
    parent = walk(doc, toks[:-1])
    last = toks[-1]
    if op['op'] == 'replace':
        existed = (0 <= int(last) < len(parent)) if isinstance(parent, list) else last in parent
        stats['replace_missing'] += 0 if existed else 1
        if isinstance(parent, list):
            parent[int(last)] = copy.deepcopy(op['value'])
        else:
            parent[last] = copy.deepcopy(op['value'])
    elif op['op'] == 'addmerge':
        if isinstance(parent, dict):
            if last in parent:
                parent[last] = merge(parent[last], op['value'])
            else:
                parent[last] = copy.deepcopy(op['value'])
        else:
            parent[int(last)] = merge(parent[int(last)], op['value'])
    else:
        raise ValueError(op['op'])


def lang_insert(orig_text, newkeys):
    """Append keys before the final closing brace, preserving original text."""
    i = orig_text.rstrip().rfind('}')
    head = orig_text[:i].rstrip()
    tail = orig_text[i:]
    if not head.endswith(',') and not head.endswith('{'):
        head += ','
    lines = ['  %s: %s' % (json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False)) for k, v in newkeys.items()]
    return head + '\n' + ',\n'.join(lines) + '\n' + tail


def main():
    os.makedirs(OUT, exist_ok=True)
    A = zipfile.ZipFile(ADDON)
    patches = parse(A.read('assets/fotsagapfill/patches/gapfill.json'))
    summary = {}
    for dom, pack in PACKS.items():
        src = zipfile.ZipFile(os.path.join(MODS, pack + '.zip'))
        names = src.namelist()
        assert len(names) == len(set(names)), 'dup entries ' + pack
        newdata = {}  # name -> bytes (replacements)
        stats = collections.Counter()
        # entity/item/recipe patches
        byfile = collections.OrderedDict()
        biomes_ops = []
        for op in patches:
            d, rel = op['file'].split(':', 1)
            if d != dom:
                continue
            if op.get('side') == 'Server' and any(x.get('modid') == 'biomes' for x in op.get('dependsOn', [])):
                nop = {k: copy.deepcopy(v) for k, v in op.items()}
                biomes_ops.append(nop)
                continue
            byfile.setdefault('assets/%s/%s' % (d, rel), []).append(op)
        for fn, ops in byfile.items():
            doc = parse(src.read(fn))
            for op in ops:
                apply_op(doc, op, stats)
            newdata[fn] = (json.dumps(doc, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
            stats['ops'] += len(ops)
        # biomes patch file (the pack's own realm declaration)
        bfn = 'assets/%s/patches/biomes.json' % dom
        bl = parse(src.read(bfn))
        assert isinstance(bl, list)
        bl.extend(biomes_ops)
        newdata[bfn] = (json.dumps(bl, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
        stats['biome_ops'] = len(biomes_ops)
        # lang
        lfn = 'assets/%s/lang/en.json' % dom
        newkeys = parse(A.read(lfn))
        olang = src.read(lfn).decode('utf-8-sig')
        orig_keys = parse(olang.encode())
        assert not (set(newkeys) & set(orig_keys))
        ntext = lang_insert(olang, newkeys)
        chk = parse(ntext.encode())
        assert len(chk) == len(orig_keys) + len(newkeys)
        newdata[lfn] = ntext.encode('utf-8')
        # new assets
        addfiles = []
        for n in A.namelist():
            if n.startswith('assets/%s/' % dom) and not n.endswith('/') and n != lfn:
                assert n not in names, n
                addfiles.append(n)
        # write
        outp = os.path.join(OUT, pack + '.zip')
        if os.path.exists(outp):
            os.remove(outp)
        existing_dirs = {n for n in names if n.endswith('/')}
        newdirs = []
        for n in addfiles:
            parts = n.split('/')[:-1]
            for k in range(1, len(parts) + 1):
                dn = '/'.join(parts[:k]) + '/'
                if dn not in existing_dirs and dn not in newdirs:
                    newdirs.append(dn)
        with zipfile.ZipFile(outp, 'w') as zo:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename in newdata:
                    data = newdata[info.filename]
                zi = zipfile.ZipInfo(info.filename, info.date_time)
                zi.compress_type = info.compress_type
                zi.external_attr = info.external_attr
                zi.create_system = info.create_system
                zo.writestr(zi, data)
            for dn in newdirs:
                zi = zipfile.ZipInfo(dn, (2026, 11, 1, 0, 0, 0))
                zi.external_attr = 0x10
                zo.writestr(zi, b'', compress_type=zipfile.ZIP_STORED)
            for n in addfiles:
                zi = zipfile.ZipInfo(n, (2026, 11, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                zo.writestr(zi, A.read(n))
        summary[pack] = dict(ops=stats['ops'], biome_ops=stats['biome_ops'], replace_missing=stats['replace_missing'],
                             changed_files=len(newdata), added_files=len(addfiles), added_dirs=len(newdirs), lang_new=len(newkeys),
                             patched=len(byfile))
        print(pack, summary[pack])
    json.dump(summary, open(os.path.join(OUT, '_build_summary.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
