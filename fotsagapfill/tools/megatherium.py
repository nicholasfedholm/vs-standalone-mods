"""Megatherium fixes: Stand animation (bipedal browsing posture, tail as third support) and Walk lateral foot roll."""
import os, json, copy, subprocess, csv, re, tempfile
DLL = r'shape-harness\bin\Release\net10.0\VsShapeCheck.dll'

# Hold pose of Stand (fitted with Nelder-Mead against VsShapeCheck: hind feet and the tail tip on the ground, forelimbs free).
# Rig: length axis is x, head toward -x, so a negative Z rotation raises the front of the body.
POSE = {"Body": {"rotationZ": -45}, "Neck1": {"rotationZ": 25}, "Forehead": {"rotationZ": 15}, "Hip point": {"offsetY": -2.8},
        "R Thigh": {"rotationZ": -17.2}, "L Thigh": {"rotationZ": -17.2}, "R Lowerleg": {"rotationZ": 36.2}, "L Lowerleg": {"rotationZ": 36.2},
        "R Ankle": {"rotationZ": -19.0}, "L Ankle": {"rotationZ": -19.0},
        "Tail01": {"rotationZ": 10.4}, "Tail2": {"rotationZ": -24.5}, "Tail3": {"rotationZ": 18.4},
        "R Shoulder": {"rotationZ": -25}, "L Shoulder": {"rotationZ": -25}, "R Arm": {"rotationZ": -12}, "L Arm": {"rotationZ": -12}}
Q = 100
HOLD = (25, 75)


def make_stand(pose=None, q=Q):
    pose = pose or POSE
    def kf(frame, k):
        els = {}
        for n, d in pose.items():
            e = {'offsetX': 0.0, 'offsetY': 0.0, 'offsetZ': 0.0, 'rotationX': 0.0, 'rotationY': 0.0, 'rotationZ': 0.0}
            for kk, v in d.items():
                e[kk] = round(v * k, 3)
            els[n] = e
        return {'frame': frame, 'elements': els}
    return {'name': 'Stand', 'code': 'stand', 'quantityframes': q, 'onActivityStopped': 'EaseOut', 'onAnimationEnd': 'Stop',
            'keyframes': [kf(0, 0.0), kf(HOLD[0], 1.0), kf(HOLD[1], 1.0), kf(q - 1, 0.0)]}


def run_h(shape_obj, tag, anims, frames=12):
    d = os.path.join(os.environ.get('TEMP', '.'), 'meg_' + tag)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'm.json')
    json.dump(shape_obj, open(p, 'w'))
    r = subprocess.run(['dotnet', DLL, p, '--frames', str(frames), '--anim', anims, '--out', d], capture_output=True, text=True)
    rows = list(csv.DictReader(open(os.path.join(d, 'm_anim.csv'))))
    if re.search(r'findings: [1-9]\d* error', r.stdout):
        raise RuntimeError('VsShapeCheck errors: ' + ' | '.join(l.strip() for l in r.stdout.splitlines() if 'ERROR' in l)[:400])
    return rows, r.stdout


def _grp(rows, anim, pat, frame=None):
    v = [float(r['miny']) for r in rows if r['anim'] == anim and r['hasFaces'] == '1' and re.search(pat, r['element'])
         and (frame is None or int(r['frame']) == frame)]
    return min(v)

HIND = r'^[LR] (Foot|toe|Ankle)'
FRONT = r'^[LR] (finger|Hand|Wrist)'


def lengthen_hind(shp, G, target_gap=0.0, tag='meg_hind'):
    """The 0.1.0 shape had its hind feet about 0.11 blocks above the front claws at rest (hips raised, legs not lengthened).
    Scale the hind thigh along y (pivot at the hip end) until the idle hind minimum equals the front minimum."""
    def gap(delta):
        s = copy.deepcopy(shp)
        G.remodel(s, [('scale', r'[RL] Thigh', (1.0, 1.0 + delta, 1.0), '', 'ro')])
        rows, _ = run_h(s, tag, 'idle', 2)
        return _grp(rows, 'idle', HIND) - _grp(rows, 'idle', FRONT), s
    d0, d1 = 0.0, 0.15
    g0, _ = gap(d0)
    g1, _ = gap(d1)
    for _ in range(6):
        if abs(g1) < 0.006 or g1 == g0:
            break
        d2 = d1 - (g1 - target_gap) * (d1 - d0) / (g1 - g0)
        d0, g0, d1 = d1, g1, d2
        g1, _ = gap(d1)
    g, s = gap(d1)
    shp['elements'] = s['elements']
    return d1, g


def _complete(e):
    # the game throws if only some of offsetX/Y/Z (or rotationX/Y/Z) are set on a keyframe element
    for grp in (('offsetX', 'offsetY', 'offsetZ'), ('rotationX', 'rotationY', 'rotationZ')):
        if any(k in e for k in grp):
            for k in grp:
                e.setdefault(k, 0.0)
    return e


def walk_front_fix(shp, passes=5, floor=-0.02, anim='walk'):
    """Longer forelimbs dip below the ground at the end of the stance phase. Raise the shoulder on the offending side at the
    nearest Walk keyframes by the measured deficit (iterated)."""
    w = [a for a in shp['animations'] if a['code'] == anim][0]
    q = w['quantityframes']
    for _ in range(passes):
        rows, _o = run_h(shp, 'wfix', anim, q)
        by = {}
        for r in rows:
            if r['anim'] == anim and r['hasFaces'] == '1':
                for side in 'LR':
                    if re.search(r'^%s (finger|Hand|Wrist)' % side, r['element']):
                        k = (int(r['frame']), side)
                        by[k] = min(by.get(k, 9), float(r['miny']))
        kfs = [k['frame'] for k in w['keyframes']]
        worst = 0
        for kf in w['keyframes']:
            for side in 'LR':
                near = [by[(f, side)] for f in range(kf['frame'] - 2, kf['frame'] + 3) if (f, side) in by]
                if not near:
                    continue
                d = max(0.0, floor - min(near))
                if d > 0.004:
                    worst = max(worst, d)
                    e = kf['elements'].setdefault(side + ' Shoulder', {})
                    # the shoulder frame is rotated about 75 degrees, so its x offset is the (mostly vertical) lift: ~0.052 blocks per voxel
                    e['offsetX'] = round(e.get('offsetX', 0.0) + d / 0.052, 3)
                    _complete(e)
        if worst <= 0.004:
            break
    return worst


def foot_roll(shp, deg=7.0):
    """Megatherium walked on the outer edges of its feet: roll both feet so the soles face inward (all Walk keyframes)."""
    w = [a for a in shp['animations'] if a['code'] == 'walk'][0]
    for kf in w['keyframes']:
        for side, sign in (('R', -1), ('L', 1)):
            e = kf['elements'].setdefault(side + ' Foot', {})
            e['rotationX'] = round(e.get('rotationX', 0.0) + sign * deg, 3)
            _complete(e)
    return deg


def add_stand(shp):
    shp['animations'] = [a for a in shp['animations'] if a['code'] != 'stand'] + [make_stand()]
