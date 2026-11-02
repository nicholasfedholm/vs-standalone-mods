"""Arctodus 0.2.0: own-domain entity derived from the VANILLA bear (brown type as base), not a patch of the vanilla entity.
Vanilla loader: reads the game install read-only (assets/survival); every reference to a vanilla asset in the new entity
uses the explicit `game:` prefix; every reference to our own assets uses `fotsagapfill:`. No rep() substring replace is used.
Output goes to G.EXTRA (stage paths). Nothing is written to the Mods folder or the game install."""
import os, json, copy, fnmatch, re, io
import pyjson5
import gapbuild as G

VANILLA = r'%APPDATA%\Vintagestory\assets\survival'
DOM = 'fotsagapfill'
CODE = 'arctodus'
TYPE = 'simus'
GENDERS = ('male', 'female')
SHAPE_REL = 'entity/animal/mammal/arctodus/simus-adult'
TEX_REL = 'entity/animal/mammal/arctodus/simus-adult'
# vanilla donor files (read only)
V_ENTITY = 'entities/animal/mammal/bear-adult.json'
V_SHAPE = 'shapes/entity/animal/mammal/bear/brown-adult.json'
V_TEX = ['textures/entity/animal/mammal/bear/brown-adult%d.png' % i for i in (1, 2, 3)]
V_POLAR_SHAPE = 'shapes/entity/animal/mammal/bear/polar-adult.json'

# remodel on the vanilla skeleton (names unchanged so every one of the 13 animations binds)
SHAPE_OPS = [
    ('scale', r'[RL] front leg', (1.0, 1.28, 1.0), '', 'ro'),     # longer forelimbs, hip joint fixed
    ('scale', r'[RL] back leg', (1.0, 1.28, 1.0), '', 'ro'),      # longer hindlimbs
    ('scale', 'mouth', (1.0, 1.0, 0.72), '', 'from'),             # shorter face
    ('scale', 'neck', (1.0, 1.1, 1.0), '', 'from'),
]
RECOLOR = [dict(dh=-10, ms=1.1, mv=0.85)]     # brown (mean hue 26) -> dark chestnut; real coat colour unknown
BODY_D = 4.5
TARGET_SHOULDER = 1.6                          # blocks, standing on all fours


def load_vanilla(rel):
    """read a vanilla asset (relative to assets/survival) as bytes; the game install is only read."""
    with open(os.path.join(VANILLA, rel.replace('/', os.sep)), 'rb') as f:
        return f.read()


def vjson(rel):
    return pyjson5.loads(load_vanilla(rel).decode('utf-8-sig'))


# ---------------------------------------------------------------- ByType collapse
def collapse(node, codes):
    """resolve every <field>ByType dict (first match wins, glob on the full entity code) for the brown male/female codes;
    result keeps the ByType name with {"*": v} when both genders agree, else {"*-male": vm, "*-female": vf}."""
    if isinstance(node, list):
        return [collapse(x, codes) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k.endswith('ByType') and isinstance(v, dict):
            res = {}
            for g, code in codes.items():
                for pat, val in v.items():
                    if fnmatch.fnmatchcase(code, pat):
                        res[g] = collapse(val, codes)
                        break
            if not res:
                continue
            vals = list(res.values())
            if len(res) == len(codes) and all(x == vals[0] for x in vals):
                out[k] = {'*': vals[0]}
            else:
                out[k] = {f'*-{g}': x for g, x in res.items()}
        else:
            out[k] = collapse(v, codes)
    return out


def vanilla_sounds(node, key=None):
    """add the explicit game: prefix to every vanilla sound reference (none of ours exist)."""
    if isinstance(node, str):
        if key in ('sound', 'eatSound', 'location', 'path', 'hurt', 'death', 'idle', 'leapSound') and ':' not in node and node.startswith('creature/'):
            return 'game:' + node
        return node
    if isinstance(node, list):
        return [vanilla_sounds(x, key) for x in node]
    if isinstance(node, dict):
        return {k: vanilla_sounds(v, k) for k, v in node.items()}
    return node


def is_arctodus_entity_free_of_bear_tokens(txt):
    """sanity: no leftover bear-<type> codes (the entity code is arctodus)."""
    return not re.search(r'bear-(brown|black|polar|sun|panda)', txt)


# ---------------------------------------------------------------- shape
def build_shape():
    shp = pyjson5.loads(load_vanilla(V_SHAPE).decode('utf-8-sig'))
    # torso z-stretch (voxels): the 1.6 block shoulder target is below the vanilla brown, so a 600 to 800 kg animal would end up
    # shorter than a 505 kg brown bear; lengthen the torso by 2*BODY_D voxels. Child coords are parent-from-relative: widening the
    # body box about its centre moves its subtree by -D, so the shoulders are pushed +2D to end up +D, the abdomen follows at -D.
    body = G.find_el(shp, 'body')
    body['from'][2] -= BODY_D
    body['to'][2] += BODY_D
    G.find_el(shp, 'shoulders')['from'][2] += 2 * BODY_D
    G.find_el(shp, 'shoulders')['to'][2] += 2 * BODY_D
    G.find_el(shp, 'shoulders')['rotationOrigin'][2] += 2 * BODY_D
    G.remodel(shp, SHAPE_OPS)
    shp['textures'] = {'skin': f'{DOM}:{TEX_REL}1'}
    return shp


def anim_miny(shp, anim, tag, frames=16):
    """lowest world y over `frames` samples of the animation, VsShapeCheck (game transform code)."""
    import csv, subprocess
    os.makedirs(G.TMPD, exist_ok=True)
    out = os.path.join(G.TMPD, 'out')
    os.makedirs(out, exist_ok=True)
    fp = os.path.join(G.TMPD, tag + '.json')
    json.dump(shp, open(fp, 'w'))
    subprocess.run(['dotnet', G.DLL, fp, '--out', out, '--frames', str(frames), '--anim', anim], capture_output=True, text=True)
    return min(float(r['miny']) for r in csv.DictReader(open(os.path.join(out, tag + '_frames.csv'))))


def fit_stand(shp, tag, log, donor_min=-0.182, cap=6.0):
    """the longer hindlimbs and torso dip below the donor's own Stand dip when rearing: lift body offsetY in the held keyframes
    (frame >= 30) so the lowest foot over the Stand animation matches the donor's lowest (-0.18, hind feet/tail already sit
    slightly under the floor in vanilla). Own shape copy only, capped."""
    a = G.anim_by_code(shp, 'stand')
    mn0 = anim_miny(shp, 'stand', tag, 28)
    lift = 0.0
    for _ in range(3):
        mn = anim_miny(shp, 'stand', tag, 28)
        if mn >= donor_min - 0.02 or lift >= cap:
            break
        step = min(cap - lift, (donor_min - mn) * 16.0 * 1.15)
        for kf in a['keyframes']:
            if kf['frame'] >= 30 and 'body' in kf['elements'] and 'offsetZ' in kf['elements']['body']:
                kf['elements']['body']['offsetZ'] += step
        lift += step
    log.append(f'stand: min y {mn0:+.3f} -> {anim_miny(shp, "stand", tag, 28):+.3f} (donor {donor_min:+.3f}); body offsetZ lift {lift:.2f} voxels in held frames')
    return lift


def shoulder_metrics(shp, tag):
    """model-space (blocks, before entity size): shoulders top y, eye y, total height, over the idle animation, after grounding."""
    import csv, subprocess
    os.makedirs(G.TMPD, exist_ok=True)
    out = os.path.join(G.TMPD, 'out')
    os.makedirs(out, exist_ok=True)
    fp = os.path.join(G.TMPD, tag + '.json')
    json.dump(shp, open(fp, 'w'))
    subprocess.run(['dotnet', G.DLL, fp, '--out', out, '--static-only'], capture_output=True, text=True)
    rows = list(csv.DictReader(open(os.path.join(out, tag + '_static.csv'))))
    get = lambda n: [r for r in rows if r['name'] == n and r['hasFaces'] == '1']
    sh = get('shoulders')[0]
    eye = (get('R eyeSlit') or get('R eye') or get('head'))[0]
    allmax = max(float(r['maxy']) for r in rows if r['hasFaces'] == '1')
    allmin = min(float(r['miny']) for r in rows if r['hasFaces'] == '1')
    return dict(shoulder_top=float(sh['maxy']), eye_y=(float(eye['miny']) + float(eye['maxy'])) / 2, top=allmax, bottom=allmin,
                length=max(max(float(r[hi]) for r in rows if r['name'] in ('abdomen', 'shoulders')) - min(float(r[lo]) for r in rows if r['name'] in ('abdomen', 'shoulders'))
                           for lo, hi in (('minx', 'maxx'), ('minz', 'maxz'))))


def own_entity(spec):
    base = vjson(V_ENTITY)
    brown_codes = {g: f'bear-brown-adult-{g}' for g in GENDERS}
    ent = collapse(base, brown_codes)
    ent['code'] = CODE
    ent['variantgroups'] = [{'code': 'type', 'states': [TYPE]}, {'code': 'age', 'states': ['adult']},
                            {'code': 'gender', 'states': list(GENDERS)}]
    # ---- shape and ground
    shp = build_shape()
    G.ground_shift(shp, 'arctodus_adult')
    spec.setdefault('_log', [])
    fit_stand(shp, 'arctodus_stand', spec['_log'])
    donor_shape = pyjson5.loads(load_vanilla(V_SHAPE).decode('utf-8-sig'))
    G.ground_shift(donor_shape, 'arctodus_donorbrown')          # donor brown, own framing, only for comparison numbers
    m = shoulder_metrics(shp, 'arctodus_m')
    md = shoulder_metrics(donor_shape, 'arctodus_md')
    pol = pyjson5.loads(load_vanilla(V_POLAR_SHAPE).decode('utf-8-sig'))
    G.ground_shift(pol, 'arctodus_polar')
    mp = shoulder_metrics(pol, 'arctodus_mp')
    # entity size so the shoulders reach TARGET_SHOULDER blocks (female; male is 10 percent bigger, as brown 0.95 : 1.05)
    size_f = round(TARGET_SHOULDER / m['shoulder_top'], 3)
    size_m = round(size_f * 1.05 / 0.95, 3)
    sh_f, sh_m = m['shoulder_top'] * size_f, m['shoulder_top'] * size_m
    spec['_measured'] = dict(model=m, brown=md, polar=mp, size_f=size_f, size_m=size_m, shoulder_f=round(sh_f, 3), shoulder_m=round(sh_m, 3),
                             brown_shoulder_blocks=round(md['shoulder_top'] * 1.05, 3), polar_shoulder_blocks=round(mp['shoulder_top'] * 1.05, 3))
    cl = ent['client']
    cl['sizeByType'] = {'*-female': size_f, '*-male': size_m}
    cl['shape'] = {'base': f'{DOM}:{SHAPE_REL}'}
    cl['texture'] = {'base': f'{DOM}:{TEX_REL}*'}
    # ---- stats the spec fixes
    ent['weightByType'] = {'*-female': 600, '*-male': 800}
    ent['eyeHeightByType'] = {'*-female': round(m['eye_y'] * size_f, 2), '*-male': round(m['eye_y'] * size_m, 2)}
    # collision/selection boxes follow the vanilla ratios to shoulder height (brown collision y / brown shoulder blocks)
    bcol_y = base['collisionBoxSizeByType']['*-male']['y']
    ratio = bcol_y / (md['shoulder_top'] * 1.05)
    ent['collisionBoxSizeByType'] = {'*-female': {'x': 1.5, 'y': round(sh_f * ratio, 2)}, '*-male': {'x': 1.65, 'y': round(sh_m * ratio, 2)}}
    ent['deadCollisionBoxSizeByType'] = {'*-female': {'x': 1.4, 'y': 0.75}, '*-male': {'x': 1.55, 'y': 0.8}}
    ent['selectionBoxSizeByType'] = {'*': {'x': 2.0, 'y': round(sh_m * 1.45, 2)}}
    ent['deadSelectionBoxSizeByType'] = {'*': {'x': 1.8, 'y': 1.2}}
    # ---- drops: generic game items only (no bear species in names)
    for b in ent['server']['behaviors']:
        if b['code'] == 'harvestable':
            for d in b['drops']:
                if d['code'].startswith('hide-raw-bear'):
                    d['code'] = 'hide-raw-huge'
                d['code'] = 'game:' + d['code']
    # ---- handbook group
    ent['attributes']['handbook'] = {'groupcode': 'creaturegroup-arctodus', 'trappableGroupCode': 'creaturegroup-arctodus-{age}'}
    ent['attributes']['biorealm'] = list(spec['realm'])
    # ---- spawn: keep the existing climate/home of the staged spec
    sc = ent['server']['spawnconditions']
    clim = spec['climate']
    sc['worldgen'].pop('insideBlockCodesByType', None)
    sc['worldgen']['insideBlockCodes'] = ['air', 'tallgrass-*', 'snowlayer-*', 'flower-*']
    sc['runtime'].pop('insideBlockCodesByType', None)
    sc['runtime']['insideBlockCodes'] = ['air', 'tallgrass-*', 'snowlayer-*', 'flower-*']
    sc['runtime']['maxQuantityByGroup'] = {'code': 'arctodus-*', 'maxQuantity': 2}
    cc = {'maxY': 1.6}
    cc.update(clim)
    sc['climate'] = cc
    # ---- rename sound references to the explicit game: domain
    for side in ('client', 'server'):
        ent[side] = vanilla_sounds(ent[side])
    ent['sounds'] = vanilla_sounds(ent['sounds'])
    # ---- health on BOTH sides (house rule); the donor bear has no gait behavior to copy, so gait is not added (recorded)
    hp = [b for b in ent['server']['behaviors'] if b['code'] == 'health'][0]
    if not any(b['code'] == 'health' for b in ent['client']['behaviors']):
        ent['client']['behaviors'].append(copy.deepcopy(hp))
    txt = json.dumps(ent)
    assert is_arctodus_entity_free_of_bear_tokens(txt), re.findall(r'.{30}bear-(?:brown|black|polar|sun|panda).{30}', txt)[:3]
    # ---- write
    bio = f'assets/{DOM}/'
    G.EXTRA[bio + 'entities/animal/mammal/arctodus-adult.json'] = json.dumps(ent, indent=1)
    G.EXTRA[bio + 'shapes/' + SHAPE_REL + '.json'] = json.dumps(shp, indent=1)
    for i, rel in enumerate(V_TEX, 1):
        png, size = G.recolor(load_vanilla(rel), RECOLOR)
        G.EXTRA[bio + f'textures/{TEX_REL}{i}.png'] = png
    nm = spec['common_name']
    lang = {
        'item-creature-arctodus-simus-adult-female': f'{nm} (Female)',
        'item-creature-arctodus-simus-adult-male': f'{nm} (Male)',
        'item-dead-creature-arctodus-simus-adult-female': f'Dead {nm} (Female)',
        'item-dead-creature-arctodus-simus-adult-male': f'Dead {nm} (Male)',
        'game:prefixandcreature-arctodus-simus-adult-*': 'a giant short-faced bear',
        'game:prefixandcreature-arctodussimusadultfemale': 'a giant short-faced bear',
        'game:prefixandcreature-arctodussimusadultmale': 'a giant short-faced bear',
        'creaturegroup-arctodus': nm,
        'game:creaturegroup-arctodus': nm,
    }
    G.EXTRA[bio + 'lang/en.json'] = json.dumps(lang, indent=1, ensure_ascii=False)
    spec['_ent'] = ent
