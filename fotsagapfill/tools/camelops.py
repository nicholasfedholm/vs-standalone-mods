"""Camelops helpers: gait phase analysis from hoof positions (VsShapeCheck boxes) and the pacing retime of the right hind legs."""
import os, sys, json, csv, subprocess, tempfile, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
DLL = r'shape-harness\bin\Release\net10.0\VsShapeCheck.dll'
HOOF = {'LF': 'L Front Hoof', 'RF': 'R Front Hoof', 'LH': 'L Hind Hoof', 'RH': 'R Hind Hoof'}


def run_h(shape_obj, tag, anims, frames=40):
    d = os.path.join(os.environ.get('TEMP', '.'), 'cam_' + tag)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'm.json')
    json.dump(shape_obj, open(p, 'w'))
    r = subprocess.run(['dotnet', DLL, p, '--frames', str(frames), '--anim', anims, '--out', d], capture_output=True, text=True)
    if ' 0 error' not in r.stdout and 'findings: 0 error' not in r.stdout:
        import re
        m = re.search(r'findings: (\d+) error', r.stdout)
        if m and int(m.group(1)) > 0:
            raise RuntimeError(r.stdout[-600:])
    return list(csv.DictReader(open(os.path.join(d, 'm_anim.csv')))), r.stdout


def hoof_series(rows, anim):
    out = {}
    for k, el in HOOF.items():
        pts = sorted((int(r['frame']), (float(r['minx']) + float(r['maxx'])) / 2) for r in rows
                     if r['anim'].lower() == anim and r['element'] == el)
        out[k] = np.array([p[1] for p in pts])
    return out


def phase(shape_obj, anim, tag, frames=40):
    rows, _ = run_h(shape_obj, tag, anim, frames)
    s = hoof_series(rows, anim)
    n = min(len(v) for v in s.values())
    s = {k: v[:n] - v[:n].mean() for k, v in s.items()}
    c = lambda a, b: float(np.corrcoef(s[a], s[b])[0, 1])
    return dict(n=n, LF_LH=round(c('LF', 'LH'), 2), RF_RH=round(c('RF', 'RH'), 2), LF_RF=round(c('LF', 'RF'), 2),
                LH_RH=round(c('LH', 'RH'), 2), LF_RH=round(c('LF', 'RH'), 2), RF_LH=round(c('RF', 'LH'), 2))


def rot_series(shp, anim, el, ch='rotationX'):
    a = [x for x in shp['animations'] if x['code'].lower() == anim][0]
    Q = a['quantityframes']
    pts = sorted((kf['frame'], kf['elements'][el][ch]) for kf in a['keyframes'] if el in kf['elements'] and ch in kf['elements'][el])
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    t = np.arange(Q)
    return np.interp(t, xs, ys)


def audit_r(shp, anim='walk'):
    s = {k: rot_series(shp, anim, e) for k, e in (('FL', 'L ArmLow'), ('FR', 'R ArmLow'), ('HL', 'L LegLow'), ('HR', 'R LegLow'))}
    c = lambda a, b: round(float(np.corrcoef(s[a], s[b])[0, 1]), 2)
    return dict(FL_FR=c('FL', 'FR'), FL_HL=c('FL', 'HL'), FR_HR=c('FR', 'HR'), FL_HR=c('FL', 'HR'), FR_HL=c('FR', 'HL'))


GROUPS = (('offsetX', 'offsetY', 'offsetZ'), ('rotationX', 'rotationY', 'rotationZ'))


def retime(shp, anim, regex, delta):
    """circularly shift the keyframes of the matched elements by delta frames (later = positive); other elements untouched."""
    import re
    a = [x for x in shp['animations'] if x['code'].lower() == anim][0]
    Q = a['quantityframes']
    kfs = {kf['frame']: kf for kf in a['keyframes']}
    names = sorted({e for kf in a['keyframes'] for e in kf['elements'] if re.fullmatch(regex, e)})
    for el in names:
        for grp in GROUPS:
            pts = sorted((kf['frame'], [kf['elements'][el][c] for c in grp]) for kf in a['keyframes']
                         if el in kf['elements'] and all(c in kf['elements'][el] for c in grp))
            if not pts:
                continue
            # strip the group from every keyframe
            for kf in a['keyframes']:
                e = kf['elements'].get(el)
                if e:
                    for c in grp:
                        e.pop(c, None)
                    if not e:
                        del kf['elements'][el]
            xs = [p[0] for p in pts]
            vs = np.array([p[1] for p in pts], float)

            def f(t):  # circular piecewise-linear
                xx = np.array(xs + [xs[0] + Q], float)
                vv = np.vstack([vs, vs[:1]])
                t = t % Q
                if t < xs[0]:
                    t += Q
                return [float(np.interp(t, xx, vv[:, i])) for i in range(3)]
            newf = sorted({(x + delta) % Q for x in xs} | {0})
            for nf in newf:
                v = f(nf - delta)
                kf = kfs.get(nf)
                if kf is None:
                    kf = {'frame': nf, 'elements': {}}
                    kfs[nf] = kf
                    a['keyframes'].append(kf)
                e = kf['elements'].setdefault(el, {})
                for c, val in zip(grp, v):
                    e[c] = round(val, 4)
    a['keyframes'].sort(key=lambda k: k['frame'])
    return names


def _circ(pts, Q):
    """pts: sorted [(frame, [x,y,z])] -> callable circular piecewise-linear"""
    xs = [p[0] for p in pts]
    vs = np.array([p[1] for p in pts], float)
    xx = np.array(xs + [xs[0] + Q], float)
    vv = np.vstack([vs, vs[:1]])

    def f(t):
        t = t % Q
        if t < xs[0]:
            t += Q
        return np.array([np.interp(t, xx, vv[:, i]) for i in range(3)])
    return f


def add_offset_y(shp, anim, el, corr):
    """corr: {frame: voxels} added to the circular offset curve of element el (all three offset channels written)."""
    a = [x for x in shp['animations'] if x['code'].lower() == anim][0]
    Q = a['quantityframes']
    grp = GROUPS[0]
    kfs = {kf['frame']: kf for kf in a['keyframes']}
    pts = sorted((kf['frame'], [kf['elements'][el][c] for c in grp]) for kf in a['keyframes']
                 if el in kf['elements'] and all(c in kf['elements'][el] for c in grp))
    f = _circ(pts, Q) if pts else (lambda t: np.zeros(3))
    cf = sorted(corr)
    cx = np.array(cf + [cf[0] + Q], float)
    cv = np.array([corr[k] for k in cf] + [corr[cf[0]]], float)

    def c(t):
        t = t % Q
        if t < cf[0]:
            t += Q
        return float(np.interp(t, cx, cv))
    frames = sorted({p[0] for p in pts} | set(cf) | {0})
    for kf in a['keyframes']:
        e = kf['elements'].get(el)
        if e:
            for ch in grp:
                e.pop(ch, None)
            if not e:
                del kf['elements'][el]
    for fr in frames:
        v = f(fr)
        v[1] += c(fr)
        kf = kfs.get(fr)
        if kf is None:
            kf = {'frame': fr, 'elements': {}}
            kfs[fr] = kf
            a['keyframes'].append(kf)
        e = kf['elements'].setdefault(el, {})
        for ch, val in zip(grp, v):
            e[ch] = round(float(val), 4)
    a['keyframes'].sort(key=lambda k: k['frame'])


def hind_ground_fix(shp, anim='walk', floor=-0.04, passes=4, frames=40):
    """lift each hind chain (Haunch offsetY) on the frames where its hooves sink below floor; returns residual per side"""
    res = {}
    for side in 'LR':
        total = {}
        for _ in range(passes):
            rows, _o = run_h(shp, 'hg', anim, frames)
            per = {}
            for r in rows:
                if r['anim'].lower() == anim and r['element'].startswith(f'{side} Hind Hoof'):
                    fr = int(r['frame'])
                    per[fr] = min(per.get(fr, 9), float(r['miny']))
            worst = min(per.values())
            if worst >= floor - 0.002:
                break
            corr = {fr: max(0.0, (floor - y) * 16.0) for fr, y in per.items()}
            for fr, v in corr.items():
                total[fr] = total.get(fr, 0.0) + v
            add_offset_y(shp, anim, f'{side} Haunch', {fr: v for fr, v in corr.items()})
        res[side] = round(worst, 4)
    return res


def add_rot(shp, anim, el, dx=0.0, dy=0.0, dz=0.0):
    """add a constant rotation (degrees) to element el over the whole animation (all rotation keys; creates frame 0 if none)."""
    a = [x for x in shp['animations'] if x['code'].lower() == anim][0]
    n = 0
    for kf in a['keyframes']:
        e = kf['elements'].get(el)
        if e and any(c in e for c in GROUPS[1]):
            for c, d in zip(GROUPS[1], (dx, dy, dz)):
                e[c] = round(e.get(c, 0.0) + d, 4)
            n += 1
    if n == 0:
        kf = next((k for k in a['keyframes'] if k['frame'] == 0), None)
        if kf is None:
            kf = {'frame': 0, 'elements': {}}
            a['keyframes'].insert(0, kf)
        e = kf['elements'].setdefault(el, {})
        for c, d in zip(GROUPS[1], (dx, dy, dz)):
            e[c] = round(e.get(c, 0.0) + d, 4)
        n = 1
    return n


def head_stats(shp, anims, frames=30, tag='hs'):
    rows, _ = run_h(shp, tag, ','.join(anims), frames)
    out = {}
    for an in anims:
        def ser(el):
            return np.array([((float(r['miny']) + float(r['maxy'])) / 2, (float(r['minx']) + float(r['maxx'])) / 2)
                             for r in rows if r['anim'].lower() == an and r['element'] == el])
        h, ch = ser('Head'), ser('Chest')
        out[an] = dict(dy=round(float((h[:, 0] - ch[:, 0]).mean()), 2), dx=round(float((h[:, 1] - ch[:, 1]).mean()), 2),
                       ymin=round(float(h[:, 0].min()), 2))
    return out


def frame_min(shape_obj, tag, anim, frames):
    """per animation frame lowest y over all solid elements (VsShapeCheck _frames.csv), {frame: miny}"""
    d = os.path.join(os.environ.get('TEMP', '.'), 'cam_' + tag)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'm.json')
    json.dump(shape_obj, open(p, 'w'))
    subprocess.run(['dotnet', DLL, p, '--frames', str(frames), '--anim', anim, '--out', d], capture_output=True, text=True)
    return {int(r['frame']): float(r['miny']) for r in csv.DictReader(open(os.path.join(d, 'm_frames.csv'))) if r['anim'].lower() == anim}


def match_donor_ground(shp, donor, anim, root, tol=0.01):
    """root offsetY correction so the per-frame lowest y follows the donor's per-frame lowest y (keeps the donor's own bob); returns (before, after) worst-min and max"""
    Q = [x for x in shp['animations'] if x['code'].lower() == anim][0]['quantityframes']
    dm = frame_min(donor, 'mgd', anim, Q)
    bm = frame_min(shp, 'mgb', anim, Q)
    corr = {fr: (dm[fr] - bm[fr]) * 16.0 for fr in bm if fr in dm and abs(dm[fr] - bm[fr]) > tol}
    before = (round(min(bm.values()), 3), round(max(bm.values()), 3))
    if corr:
        full = {fr: corr.get(fr, 0.0) for fr in bm}
        add_offset_y(shp, anim, root, full)
    am = frame_min(shp, 'mga', anim, Q)
    return before, (round(min(am.values()), 3), round(max(am.values()), 3)), (round(min(dm.values()), 3), round(max(dm.values()), 3))
