"""Ground-contact check. For each built species shape (adult + baby) run VsShapeCheck and report the lowest world y
(blocks, model space before entity size scale) over Idle and Walk frames, built vs donor.
Usage: python -I work/groundcheck.py [species ids...] [--anims idle,walk,...]  (reads work/stage, donor zips read-only)"""
import os, sys, re, csv, json, zipfile, subprocess, tempfile, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'work'))
import specs
DLL = r'shape-harness\bin\Release\net10.0\VsShapeCheck.dll'
MODS = r'%APPDATA%\VintagestoryData\Mods'
STAGE = os.path.join(ROOT, 'work', 'stage')
TMP = os.environ.get('GC_TMP') or os.path.join(os.environ.get('TEMP', '.'), 'gc_tmp')
LO, HI = -0.05, 0.05


def run(shape_path, tag, anims, frames=8):
    out = os.path.join(TMP, tag)
    os.makedirs(out, exist_ok=True)
    cmd = ['dotnet', DLL, shape_path, '--frames', str(frames), '--out', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    errs = re.search(r'findings: (\d+) error, (\d+) warn', r.stdout)
    base = os.path.splitext(os.path.basename(shape_path))[0]
    res = {}
    fp = os.path.join(out, base + '_frames.csv')
    if os.path.exists(fp):
        for row in csv.DictReader(open(fp)):
            a = row['anim'].lower()
            if a in anims:
                res.setdefault(a, []).append(float(row['miny']))
    return res, (errs.groups() if errs else ('?', '?')), os.path.join(out, base + '_static.csv')


def gaps(static_csv):
    rows = list(csv.DictReader(open(static_csv)))
    by = {int(r['idx']): r for r in rows}
    out = {}
    def box(r): return [float(r[k]) for k in ('minx','miny','minz','maxx','maxy','maxz')]
    for r in rows:
        if r['hasFaces'] != '1': continue
        p = r['parent']
        try: p = int(p)
        except: continue
        while p in by and by[p]['hasFaces'] != '1':
            try: p = int(by[p]['parent'])
            except: p = -1
        if p not in by: continue
        a, b = box(r), box(by[p])
        g = max(0.0, max(max(a[i] - b[i+3], b[i] - a[i+3]) for i in range(3)))
        out[r['name']] = g
    return out


def summarize(res):
    out = {}
    for a, v in res.items():
        out[a] = (min(v), max(v))
    return out


def shapes_for(s, donor_map=None):
    new, old = s['new_type'], s['donor_type']
    found = []
    for p in glob.glob(os.path.join(STAGE, 'assets', '*', 'shapes', 'entity', '**', '*.json'), recursive=True):
        rp = p.replace(chr(92), '/')
        if new in rp and 'antlers' not in rp:
            found.append(rp)
    return sorted(found)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    anims = {'idle', 'walk'}
    if '--anims' in sys.argv:
        anims = set(sys.argv[sys.argv.index('--anims') + 1].split(','))
        args = [a for a in args if a != sys.argv[sys.argv.index('--anims') + 1]]
    sel = [s for s in specs.SPECS if not args or s['id'] in args]
    rows = []
    fails = 0
    for s in sel:
        z = None
        dzip = s['donor_zip']
        if dzip and os.path.exists(os.path.join(MODS, dzip)):
            z = zipfile.ZipFile(os.path.join(MODS, dzip))
        for sp in shapes_for(s):
            rel = sp.split('/assets/')[1]
            label = rel.split('/shapes/entity/')[1]
            res, e, bst = run(sp, f"{s['id']}_{os.path.basename(sp)[:-5]}_b", anims)
            dst = None
            dres = {}
            dpath = 'assets/' + rel.replace(s['new_type'], s['donor_type'])
            for ex in s.get('extra_assets', []):
                if ex['dst'] == 'assets/' + rel:
                    dpath = ex['src']
            if s.get('donor_shape_file') and label.endswith('-adult.json'):
                dres, _, dst = run(s['donor_shape_file'], f"{s['id']}_{os.path.basename(sp)[:-5]}_d", anims)
            elif z and dpath in z.namelist():
                tf = os.path.join(TMP, 'donor_' + s['id'] + '_' + os.path.basename(dpath))
                os.makedirs(TMP, exist_ok=True)
                open(tf, 'wb').write(z.read(dpath))
                dres, _, dst = run(tf, f"{s['id']}_{os.path.basename(sp)[:-5]}_d", anims)
            b, d = summarize(res), summarize(dres)
            ok = None
            if b:
                idle = b.get('idle'); walk = b.get('walk'); dw = d.get('walk')
                lo_w = min(LO, (dw[0] - 0.02) if dw else LO)
                ok = (idle is None or LO <= idle[0] <= HI) and (walk is None or (lo_w <= walk[0] <= HI))
            if ok is False:
                fails += 1
            bad = None
            if dst:
                try:
                    bg, dg = gaps(bst), gaps(dst)
                    bad = [n for n, g in bg.items() if g > dg.get(n, 0) + 0.07]
                except Exception as ex:
                    bad = ['gapcheck-error']
            rows.append((s['id'], label, e, b, d, ok, bad))
    for sid, label, e, b, d, ok, bad in rows:
        bs = ' '.join(f"{a}:{v[0]:+.3f}/{v[1]:+.3f}" for a, v in sorted(b.items()))
        ds = ' '.join(f"{a}:{v[0]:+.3f}/{v[1]:+.3f}" for a, v in sorted(d.items()))
        print(f"{'PASS' if ok else 'FAIL' if ok is False else 'NOANIM'} {sid} {label[-48:]} err/warn={e[0]}/{e[1]} built[{bs}] donor[{ds}] detached={bad if bad is None else (len(bad), bad[:4])}")
    print('ground-contact fails:', fails, 'of', len(rows), 'shapes (range', LO, HI, 'min/max of per-frame lowest y)')


if __name__ == '__main__':
    main()
