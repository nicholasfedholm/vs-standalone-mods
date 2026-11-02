"""0.2.0 fact-fix hooks: per-species spec overrides and post hooks (attached over work/specs.py)."""
import os, re, json, copy, io
import gapbuild as G

KIWI = 'creature/apterygidae/male-apteryx*'
CASS = 'casuariidae:creature/casuariidae/cassgrunt*'


def attach(SPECS):
    by = {s['id']: s for s in SPECS}
    for sid, fn in FIX.items():
        if sid in by:
            fn(by[sid])


def adult_shape(ctx, suffix='-adult.json'):
    k = [p for p in ctx.d.assets if '/shapes/entity/' in p and p.endswith(f'{ctx.new}{suffix}')]
    return json.loads(ctx.d.assets[k[0]].decode('utf8')) if k else None


def bytype_set(doc_side, field, key, val):
    """set key (existing, renamed from donor) in a ByType dict if present."""
    d = doc_side.get(field)
    if isinstance(d, dict) and key in d:
        d[key] = val
        return True
    return False


# ---------------------------------------------------------------- 1 aepyornis
def aepyornis(s):
    ops = [('scale', 'Body', (1.0, 1.25, 1.35), 'z'), ('scale', 'Neck1', (0.72, 1.15, 1.2), 'z'),
           ('scale', '[LR]Thigh', (1.1, 0.9, 1.35), 'z', 'ro'), ('scale', '[LR]Foot', (1.0, 1.0, 1.3), 'z')]
    s['shape_ops'] = ops
    s['baby_ops'] = ops
    s['ground'] = True
    base = 'assets/dinornithidae/'
    s['extra_assets'] = [
        dict(src=base + 'shapes/entity/animal/bird/dinornithidae/dinornisnovaezealandiae-baby.json',
             dst=base + 'shapes/entity/animal/bird/dinornithidae/aepyornismaximus-baby.json', kind='shape_baby'),
        dict(src=base + 'textures/entity/animal/bird/dinornithidae/dinornisnovaezealandiae-baby.png',
             dst=base + 'textures/entity/animal/bird/dinornithidae/aepyornismaximus-baby.png', kind='png')]
    s['donor_why_v2'] = 'chick shape/texture now own aepyornismaximus-baby clones (same remodel/recolor); kiwi (sister group) call; 3 m standing height'
    s['target_height'] = 3.0

    def post(ctx):
        P = 'entity/animal/bird/dinornithidae/'
        n = ctx.repoint({P + 'dinornisnovaezealandiae-baby': P + 'aepyornismaximus-baby'})
        # sounds: idle = kiwi call (kiwi are the living sister group of elephant birds); hurt/death = cassowary grunt (PLACEHOLDER)
        ctx.repoint({'creature/dinornithidae/southcall*': KIWI, 'creature/dinornithidae/hiss': CASS, 'creature/dinornithidae/hurt': CASS})
        shp = adult_shape(ctx)
        m = G.measure(shp, 'aep_h')
        H = m['maxy'] - m['miny']
        size_f = round(3.0 / H, 3)
        size_m = round(size_f * 0.88, 3)
        ctx.spec['_measured'] = dict(shape_height=round(H, 3), size_f=size_f, size_m=size_m)
        rel = 'entities/animal/bird/dinornithidae-adult.json'
        doc = ctx.doc(rel)
        t = ctx.new
        cl = doc['client']['sizeByType']
        cl[f'*-adult-female-{t}'] = size_f
        cl[f'*-adult-male-{t}'] = size_m
        ctx.mark(rel, 'client', 'sizeByType')
        for fld, kf, km in (('hitBoxSizeByType', {'x': 2.1, 'y': 2.9}, {'x': 1.85, 'y': 2.55}),
                            ('deadhitBoxSizeByType', {'x': 2.1, 'y': 1.2}, {'x': 1.85, 'y': 1.05})):
            d = doc[fld]
            d[f'*-adult-female-{t}'] = kf
            d[f'*-adult-male-{t}'] = km
            ctx.mark(rel, fld)
        e = doc['eyeHeightByType']
        e[f'*-adult-female-{t}'] = 2.7
        e[f'*-adult-male-{t}'] = 2.38
        ctx.mark(rel, 'eyeHeightByType')
    s['post'] = post


# ---------------------------------------------------------------- 2 doedicurus
GEN_IDLE = 'game:creature/hooved/generic/sniff'
GEN_CALL = 'game:creature/hooved/generic/call*'


def doedicurus(s):
    ops = [('scale', 'Shell Back', (1.2, 1.9, 1.15), 'z'),
           ('scale', 'Tail1', (1.35, 1.5, 1.5), 'yz'), ('scale', 'Tail6', (1.6, 2.2, 2.2), 'yz'),
           ('scale', '[RL] Lowerleg', (1.4, 1.3, 1.4), 'xz'), ('scale', '[RL] Lowerarm', (1.4, 1.3, 1.4), 'xz')]
    # the adult also drops the horn pairs (the baby has no horn elements) and lifts the belly (a no-op once the shape is re-grounded)
    s['shape_ops'] = [('drop', r'[RL] Horn (1|base)')] + ops + [('move', 'Shell Belly', (0, 2.4, 0))]
    s['baby_ops'] = ops
    s['ground'] = True

    def shape_fn(shp, kind):
        # limb sprawl: walk/swim rotationZ of the arm and leg segments to 25 percent of the donor (own shape copy only)
        for anim in ('walk', 'swim'):
            G.anim_scale_rot(shp, anim, r'[RL] (Forearm|Lowerarm|Lowerleg)', 'Z', 0.25)
    s['shape_fn'] = shape_fn
    s['donor_why_v2'] = ('live birth (inferred; no fossil reproduction data), limb sprawl 25 percent, generic hooved sounds (PLACEHOLDER), '
                         'own shell item, hornless remodelled calf')

    def post(ctx):
        new = ctx.new
        er = 'entities/animal/reptile/meiolaniidae-adult.json'
        doc = ctx.doc(er)
        # 1 no egg laying for this variant
        for bi, b in enumerate(doc['server']['behaviors']):
            if b['code'] == 'taskai':
                for ti, t in enumerate(b['aitasks']):
                    if t['code'] == 'seekblockandlay':
                        ebt = t.get('enabledByType') or {'*': True}
                        t['enabledByType'] = {**{f'*-{new}': False}, **ebt}
                        for k, v in list(t.items()):
                            if isinstance(v, dict) and k != 'enabledByType':
                                for kk in [x for x in v if new in x]:
                                    del v[kk]
                        ctx.mark(er, 'server', 'behaviors', bi, 'aitasks', ti)
        # 2 female-only live birth (Vombatidae pattern); pregnancyDays 56 is a game value
        key = f'*-adult-female-{new}'
        for bi, b in enumerate(doc['server']['behaviors']):
            if b['code'] != 'multiply':
                continue
            def first(field, val):
                d = b.get(field)
                items = [(key, val)] + [(k, v) for k, v in (d or {}).items() if k != key]
                b[field] = dict(items)
            first('enabledByType', True)
            first('spawnEntityCodesByType', [{'code': f'meiolaniidae:meiolaniidae-baby-female-{{type}}'},
                                             {'code': f'meiolaniidae:meiolaniidae-baby-male-{{type}}'}])
            for fld, val in (('spawnQuantityMinByType', 1), ('spawnQuantityMaxByType', 1), ('pregnancyDaysByType', 56)):
                d = b.get(fld, {})
                b[fld] = dict([(f'*-{new}', val)] + [(k, v) for k, v in d.items() if k != f'*-{new}' and new not in k])
            # cooldowns were plain numbers shared by every variant; make them ByType, donor value as fallback
            for nm, v_new in (('multiplyCooldownDaysMin', 4), ('multiplyCooldownDaysMax', 11)):
                old = b.pop(nm, None)
                d = dict([(f'*-{new}', v_new)] + ([('*', old)] if old is not None else []))
                b[nm + 'ByType'] = d
            ctx.mark(er, 'server', 'behaviors', bi)
        # 3 remove the egg entity and egg item variants for the new type
        for rel in ('entities/animal/reptile/meiolaniidae-egg.json', 'itemtypes/eggs.json'):
            n = ctx.n(rel)
            ctx.d.cur[n] = copy.deepcopy(ctx.d.orig[n])
            ctx.d.changed[n] = set()
        for k in [k for k in ctx.d.lang_add if new in k and re.search(r'-(egg|nest)-|egg', k)]:
            del ctx.d.lang_add[k]
        # 4 calf, not hatchling
        for k, v in list(ctx.d.lang_add.items()):
            if new in k and 'hatchling' in v.lower():
                ctx.d.lang_add[k] = re.sub('Hatchling', 'Calf', re.sub('hatchling', 'calf', v))
        # 5 sounds: Manidae ships none, no xenarthran pack is installed -> generic vanilla hooved call (PLACEHOLDER)
        ctx.repoint({'creature/meiolaniidae/hiss*': GEN_CALL, 'creature/meiolaniidae/idle*': GEN_IDLE})
    s['post'] = post


# ---------------------------------------------------------------- 3 arctodus (own-domain entity from the vanilla bear)
def arctodus(s):
    import arctodus as A
    s['donor_zip'] = None
    s['donor_type'] = 'bear'
    s['new_type'] = 'arctodus'
    s['own_entity'] = A.own_entity
    s['donor_shape_file'] = os.path.join(A.VANILLA, 'shapes', 'entity', 'animal', 'mammal', 'bear', 'brown-adult.json')
    s['inject'] = {}
    s['shape_ops'] = A.SHAPE_OPS
    s['donor_why_v2'] = ('own-domain entity derived from vanilla bear-adult (brown): vanilla shape and Stand, 13 ai tasks, game:creature/bear sounds; '
                         'limbs x1.28, face z x0.72, dark chestnut; adult only (vanilla bear has no baby or breeding)')


# ---------------------------------------------------------------- 4 megatherium
def megatherium(s):
    import megatherium as MG
    tail = ('scale', 'Tail2', (1.4, 1.0, 1.0), '', 'from')       # long thick tail: the third support of the tripod stance
    adult_ops = [o for o in s['shape_ops'] if o[0] != 'move'] + [tail]
    s['shape_ops'] = s['shape_ops'] + [tail]
    s['baby_ops'] = adult_ops                                     # same remodel and (spec) recolor on the cub; the Hip point lift is a no-op once grounded
    s['ground'] = True
    s['_fit'] = {}

    def shape_fn(shp, kind):
        d, g = MG.lengthen_hind(shp, G)
        w = MG.walk_front_fix(shp)
        wr = MG.walk_front_fix(shp, floor=-0.06, anim='run')
        MG.foot_roll(shp, 10.0)
        s['_fit'][kind] = dict(thigh_y=round(d, 3), hind_gap=round(g, 4), walk_front_residual=round(w, 4), run_front_residual=round(wr, 4))
        print('megatherium fit', kind, s['_fit'][kind])
        if kind == 'adult':
            MG.add_stand(shp)
    s['shape_fn'] = shape_fn
    s['donor_why_v2'] = ('hind legs lengthened to ground (+27 percent thigh), tail x1.4, Stand (rear-up browsing, tail tripod) on own adult shape copy, '
                         'outward-edge foot roll 10 deg in Walk, generic hooved sounds (PLACEHOLDER), cub = same remodel; pelt/headmount items already own-named')

    def post(ctx):
        t = ctx.new
        ra, rb = 'entities/animal/mammal/diprotodontidae-adult.json', 'entities/animal/mammal/diprotodontidae-baby.json'
        # sounds: no sloth or xenarthran pack is installed -> neutral large-animal calls from the game (PLACEHOLDER)
        ctx.set_first(ra, ['soundsByType'], f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE})
        ctx.set_first(rb, ['soundsByType'], f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE})
        ctx.repoint({'vombatidae:creature/diprotodontidae/bellow*': GEN_CALL, 'vombatidae:creature/diprotodontidae/babycall*': GEN_CALL,
                     'vombatidae:creature/diprotodontidae/snort*': GEN_CALL, 'vombatidae:creature/diprotodontidae/idle*': GEN_IDLE})
        # Stand: client animation entry + an idle task enabled for this type only
        doc = ctx.doc(ra)
        if not any(a.get('code') == 'stand' for a in doc['client']['animations']):
            doc['client']['animations'].append({'code': 'stand', 'animation': 'stand', 'easeInSpeed': 4, 'easeOutSpeed': 3, 'weight': 1,
                                                'blendMode': 'Average'})
        ctx.mark(ra, 'client', 'animations')
        for bi, b in enumerate(doc['server']['behaviors']):
            if b['code'] == 'taskai':
                if not any(x.get('animation') == 'Stand' for x in b['aitasks']):
                    b['aitasks'].append({'code': 'idle', 'priority': 1.12, 'priorityForCancel': 2.0, 'minduration': 6000, 'maxduration': 6000,
                                         'mincooldown': 90000, 'maxcooldown': 420000, 'animation': 'Stand', 'animationSpeed': 0.7,
                                         'enabledByType': {f'*-{t}': True, '*': False}})
                ctx.mark(ra, 'server', 'behaviors', bi, 'aitasks')
    s['post'] = post

def hippopotamus_lemerlei(s):
    import re as _re
    s['baby_ops'] = list(s['shape_ops'])                 # calf = proportionate version of the adult remodel (same element names), same recolor
    s['ground'] = True
    # spawn: VS has no near-water spawn condition (only InsideBlockCodes = the block at the spawn spot, and getoutofwater would
    # pull a spawned hippo straight out of a lake). Forest is tied through climate; wetter minimum rain stands in for riparian land.
    s['climate'] = dict(s['climate'], minForest=0.15, minRain=0.45)
    def shape_fn(shp, kind):
        # shortened legs + lowered Rear: the walk bob dipped the front hooves 0.009 below the check range; halve the bob (0.4 voxel up on the bob keys)
        if kind == 'adult':
            for code, up in (('walk', 0.4), ('run', 0.8)):
                a = G.anim_by_code(shp, code)
                for kf in a.get('keyframes', []):
                    r = kf.get('elements', {}).get('Rear')
                    if r and 'offsetY' in r:
                        r['offsetY'] = round(r['offsetY'] + up, 4)
    s['shape_fn'] = shape_fn
    s['donor_why_v2'] = ('spawn climate only (no water-tie condition in VS): minForest 0.15, minRain 0.45; buffalo sounds removed (adult silent: no hippo sounds installed; '
                         'tasks fall to generic hooved sniff), calf idle sheep sound replaced, calf = adult remodel; swim and getoutofwater kept; pelt items already own-named')

    def strip(node, new):
        n = 0
        if isinstance(node, dict):
            for k in list(node):
                v = node[k]
                if isinstance(k, str) and k.startswith('@') and new in k:
                    m = _re.search(r'\(([^)]*)\)', k)
                    alts = [a for a in m.group(1).split('|') if a != new]
                    nk = k[:m.start(1)] + '|'.join(alts) + k[m.end(1):]
                    del node[k]
                    if alts:
                        node[nk] = v
                    n += 1
            for v in node.values():
                n += strip(v, new)
        elif isinstance(node, list):
            for v in node:
                n += strip(v, new)
        return n

    def post(ctx):
        t = ctx.new
        ra, rb = 'entities/animal/mammal/hooved/bovinae-adult.json', 'entities/animal/mammal/hooved/bovinae-baby.json'
        for rel in (ra, rb):
            doc = ctx.doc(rel)
            for bi, b in enumerate(doc['server']['behaviors']):
                if b['code'] != 'taskai':
                    continue
                for ti, task in enumerate(b['aitasks']):
                    sb = task.get('soundByType')
                    if isinstance(sb, dict):
                        k = strip(sb, t)
                        if k:
                            ctx.mark(rel, 'server', 'behaviors', bi, 'aitasks', ti, 'soundByType')
        # adult task 3 falls to a sheep idle through '*-adult-*': give the hippo the neutral hooved sound
        doc = ctx.doc(ra)
        for bi, b in enumerate(doc['server']['behaviors']):
            if b['code'] == 'taskai':
                for ti, task in enumerate(b['aitasks']):
                    sb = task.get('soundByType')
                    if isinstance(sb, dict) and sb.get('*-adult-*') == 'game:creature/sheep/idle':
                        ctx.set_first(ra, ['server', 'behaviors', bi, 'aitasks', ti, 'soundByType'], f'*-{t}', 'game:creature/hooved/generic/sniff*')
                        ctx.mark(ra, 'server', 'behaviors', bi, 'aitasks', ti, 'soundByType')
        # calf entity sounds: replace the sheep idle that '*-baby-*' gives every calf
        ctx.set_first(rb, ['soundsByType'], f'*-{t}', {'hurt': 'game:creature/hooved/generic/sniff*', 'death': 'game:creature/hooved/generic/sniff*',
                                                       'idle': GEN_IDLE})
    s['post'] = post


def camelops(s):
    import camelops as CM
    ops = list(s['shape_ops'])
    s['baby_ops'] = [o for o in ops if o[1] != 'Wattle']      # the moose calf rig has no Wattle element; everything else is the adult remodel
    s['ground'] = True
    base = 'assets/capreolinae/'
    sh = 'shapes/entity/animal/mammal/hooved/alceini/'
    s['extra_assets'] = [
        dict(src=base + sh + 'alcesalces/baby.json', dst=base + sh + 'camelopshesternus/baby.json', kind='shape_baby'),
        dict(src=base + 'shapes/item/animal/mammal/hooved/alceini/alcesalces/floorpelt-baby.json',
             dst=base + 'shapes/item/animal/mammal/hooved/alceini/camelopshesternus/floorpelt-baby.json', kind='raw')]
    s['_gait'] = {}

    def shape_fn(shp, kind):
        if kind != 'adult':
            return
        HR = r'R (Haunch|LegUp|LegLow|Hind Pastern|Hind Hoof\d?|LegUp Taper)'
        HL = HR.replace('R (', 'L (', 1)
        s['_gait']['before'] = CM.phase(shp, 'walk', 'wb'), CM.audit_r(shp, 'walk')
        # pacing walk: both hind legs retimed 22 of 80 frames so each hind leg moves with the front leg of its own side
        # (hoof-position phase scan: same-side r -0.28 -> +0.85/+0.92; the rotationX audit metric underestimated the left side)
        CM.retime(shp, 'walk', HR, 22)
        CM.retime(shp, 'walk', HL, 22)
        # the retimed hind legs sank 0.14 blocks; lift each hind chain (Haunch offsetY) on the sinking frames to -0.04
        s['_gait']['hind_residual'] = CM.hind_ground_fix(shp, 'walk', -0.04)
        s['_gait']['after'] = CM.phase(shp, 'walk', 'wa'), CM.audit_r(shp, 'walk')
        s['_gait']['trot'] = CM.phase(shp, 'trot', 'wt')
        print('camelops walk phase before/after', s['_gait']['before'], s['_gait']['after'], 'trot', s['_gait']['trot'])
    s['shape_fn'] = shape_fn
    s['donor_why_v2'] = ('pacing Walk (hind legs retimed 22 of 80 frames, same-side legs in phase), own calf shape clone with the adult remodel, '
                         'generic hooved calls (PLACEHOLDER, no camelid pack), calf labels; hump kept as a judgement call; Trot already diagonal, Canter/Run unchanged')

    def post(ctx):
        t = ctx.new
        ra, rb = 'entities/animal/mammal/hooved/alceini-adult.json', 'entities/animal/mammal/hooved/alceini-baby.json'
        E = 'entity/animal/mammal/hooved/alceini/'
        ctx.set_first(ra, ['soundsByType'], f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE})
        ctx.set_first(rb, ['soundsByType'], f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE})
        ctx.repoint({'capreolinae:creature/alces/cervalcesroar*': GEN_CALL, 'capreolinae:creature/alces/cervalcescall*': GEN_CALL})
        # task sounds that every alceini type shares ('*' -> moose hurt / calf calls): give this type its own first key
        for rel in (ra, rb):
            doc = ctx.doc(rel)
            for bi, b in enumerate(doc['server']['behaviors']):
                if b['code'] != 'taskai':
                    continue
                for ti, task in enumerate(b['aitasks']):
                    sb = task.get('soundByType')
                    if isinstance(sb, dict) and any('alces/' in str(v) and 'cervalces' not in str(v) and 'alcesroar' not in str(v) and 'alcescall' not in str(v)
                                                    for k, v in sb.items() if t not in k):
                        ctx.set_first(rel, ['server', 'behaviors', bi, 'aitasks', ti, 'soundByType'], f'*-{t}', GEN_CALL)
        ctx.repoint({'entity/animal/mammal/hooved/alceini/alcesalces/baby': E + f'{t}/baby',
                     'item/animal/mammal/hooved/alceini/alcesalces/floorpelt-baby': f'item/animal/mammal/hooved/alceini/{t}/floorpelt-baby'})
        for k in list(ctx.d.lang_add):
            if t in k and 'baby' in k and ctx.d.lang_add[k].endswith('(Fawn)'):
                ctx.lang(k, ctx.d.lang_add[k][:-6] + '(Calf)')
    s['post'] = post


def macrauchenia(s):
    import camelops as CM
    s['baby_ops'] = list(s['shape_ops'])
    s['ground'] = True
    base = 'assets/capreolinae/'
    sh = 'shapes/entity/animal/mammal/hooved/odocoileini/'
    s['extra_assets'] = [
        dict(src=base + sh + 'odocoileusvirginianus/baby.json', dst=base + sh + 'macraucheniapatachonica/baby.json', kind='shape_baby'),
        dict(src=base + 'shapes/item/animal/mammal/hooved/odocoileini/odocoileusvirginianus/floorpelt-baby.json',
             dst=base + 'shapes/item/animal/mammal/hooved/odocoileini/macraucheniapatachonica/floorpelt-baby.json', kind='raw')]
    s['_neck'] = {}
    # neck pitch added to the fast anims (degrees about Z; positive lowers the head forward in this rig), head counter-rotated so the muzzle stays forward
    LEVEL = {'trot': (10, -4), 'canter': (22, -9), 'stot': (22, -9), 'run': (30, -12), 'charge': (30, -12)}

    def shape_fn(shp, kind):
        have = {x['code'].lower() for x in shp['animations']}
        for an, (dn, dh) in LEVEL.items():
            if an not in have:
                continue
            CM.add_rot(shp, an, 'Neck', dz=dn)
            CM.add_rot(shp, an, 'Head', dz=dh)
        s['_neck'][kind] = CM.head_stats(shp, [a for a in ['idle', 'walk', 'trot', 'canter', 'run'] if a in have], tag='mn' + kind)
        print('macrauchenia head-minus-chest y/x', kind, s['_neck'][kind])
    s['shape_fn'] = shape_fn
    s['donor_why_v2'] = ('neck carried more level in Trot/Canter/Stot/Run/Charge (Neck +10..30 deg, Head counter -4..-12) on own shape copy, idle stays erect; '
                         'own calf shape clone with the adult remodel (nose enlarged, no trunk); generic hooved sounds (PLACEHOLDER, no litoptern pack); calf labels')

    def post(ctx):
        t = ctx.new
        ra, rb = 'entities/animal/mammal/hooved/odocoileini-adult.json', 'entities/animal/mammal/hooved/odocoileini-baby.json'
        for rel in (ra, rb):
            ctx.set_first(rel, ['soundsByType'], f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE})
        ctx.repoint({'entity/animal/mammal/hooved/odocoileini/odocoileusvirginianus/baby': f'entity/animal/mammal/hooved/odocoileini/{t}/baby',
                     'item/animal/mammal/hooved/{tribe}/odocoileusvirginianus/floorpelt-baby': f'item/animal/mammal/hooved/{{tribe}}/{t}/floorpelt-baby'})
        for k in list(ctx.d.lang_add):
            if t in k and 'baby' in k and 'awn' in ctx.d.lang_add[k]:
                ctx.lang(k, ctx.d.lang_add[k].replace('Fawn', 'Calf').replace('fawn', 'calf'))
    s['post'] = post


def toxodon(s):
    ops = list(s['shape_ops'])
    s['baby_ops'] = [o for o in ops if o[1] != 'Hump']      # the buffalo calf rig has no Hump element; the rest is the adult remodel
    s['ground'] = True
    base = 'assets/bovinae/'
    s['extra_assets'] = [
        dict(src=base + 'shapes/entity/bovinae/bubalusbubalis/baby.json', dst=base + 'shapes/entity/bovinae/toxodonplatensis/baby.json', kind='shape_baby'),
        dict(src=base + 'shapes/item/bovinae/bubalusbubalis/floorpelt-baby.json', dst=base + 'shapes/item/bovinae/toxodonplatensis/floorpelt-baby.json', kind='raw')]
    s['donor_why_v2'] = ('own calf shape clone (buffalo calf rig + adult remodel minus Hump) + floorpelt-baby clone; water buffalo moo/idle and sheep idle replaced by '
                         'generic hooved sniff/call (PLACEHOLDER, no notoungulate or toxodon sound installed); horns stay off')

    def collect(node, path, new, out):
        if isinstance(node, dict):
            if any(isinstance(k, str) and k.startswith('@') and new in k for k in node):
                out.append(path)
            for k, v in node.items():
                collect(v, path + [k], new, out)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                collect(v, path + [i], new, out)

    def strip_alt(node, new):
        for k in list(node):
            if isinstance(k, str) and k.startswith('@') and new in k:
                m = re.search(r'\(([^)]*)\)', k)
                alts = [a for a in m.group(1).split('|') if a != new]
                v = node.pop(k)
                if alts:
                    node[k[:m.start(1)] + '|'.join(alts) + k[m.end(1):]] = v

    def post(ctx):
        t = ctx.new
        for rel, idle in (('entities/animal/mammal/hooved/bovinae-adult.json', GEN_CALL), ('entities/animal/mammal/hooved/bovinae-baby.json', GEN_IDLE)):
            doc = ctx.doc(rel)
            paths = []
            collect(doc, [], t, paths)
            for pth in paths:
                node = doc
                for q in pth:
                    node = node[q]
                strip_alt(node, t)
                sample = next(iter(node.values()), None)
                tcode = doc['server']['behaviors'][pth[2]]['aitasks'][pth[4]]['code'] if len(pth) > 5 and pth[0] == 'server' else ''
                val = GEN_IDLE if tcode in ('idle', 'wander', 'stayclosetoentity') else idle
                ctx.set_first(rel, pth, f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE} if isinstance(sample, dict) else val)
            # the '*-adult-*' / '*-baby-*' sheep idle fallbacks
            for bi, b in enumerate(doc['server']['behaviors']):
                for ti, task in enumerate(b.get('aitasks', [])):
                    sb = task.get('soundByType')
                    if isinstance(sb, dict) and any(v == 'game:creature/sheep/idle' for v in sb.values()) and f'*-{t}' not in sb:
                        ctx.set_first(rel, ['server', 'behaviors', bi, 'aitasks', ti, 'soundByType'], f'*-{t}', GEN_IDLE)
        ctx.set_first('entities/animal/mammal/hooved/bovinae-baby.json', ['soundsByType'], f'*-{t}', {'hurt': GEN_CALL, 'death': GEN_CALL, 'idle': GEN_IDLE})
        ctx.repoint({'entity/bovinae/bubalusbubalis/baby': f'entity/bovinae/{t}/baby',
                     'item/bovinae/bubalusbubalis/floorpelt-baby': f'item/bovinae/{t}/floorpelt-baby'})
    s['post'] = post


def cryptoprocta(s):
    s['donor_why_v2'] = ('walk Hip bob raised 0.4 voxel (0.025 block) so the lengthened legs no longer dip below the donor walk range; civet idle* sound kept as nearest '
                         'installed feliform (no Eupleridae pack; PLACEHOLDER); pelt drops resolve to own-named Cryptoprocta Skin variants')

    def shape_fn(shp, kind):
        if kind != 'adult':
            return
        a = G.anim_by_code(shp, 'walk')
        for kf in a.get('keyframes', []):
            r = kf.get('elements', {}).get('Hip')
            if r and 'offsetY' in r:
                r['offsetY'] = round(r['offsetY'] + 0.4, 4)
    s['shape_fn'] = shape_fn


def diprotodon(s):
    import camelops as CM
    import zipfile as _zf
    s['_gnd'] = {}

    def shape_fn(shp, kind):
        if kind != 'adult':
            return
        z = _zf.ZipFile(os.path.join(G.MODS, s['donor_zip']))
        n = [x for x in z.namelist() if x.endswith('diprotodontidae/zygomaturustrilobus-adult.json')][0]
        import pyjson5 as _pj
        donor = _pj.loads(z.read(n).decode('utf-8-sig'))
        for an in ('walk', 'run'):
            s['_gnd'][an] = CM.match_donor_ground(shp, donor, an, 'Hip point')
        print('diprotodon ground (built before, after, donor) min/max:', s['_gnd'])
    s['shape_fn'] = shape_fn
    s['donor_why_v2'] = ('Walk/Run root offsetY corrected per frame to follow the donor per-frame lowest-y curve (longer legs sank 0.04 / 0.13 blocks deeper); '
                         'diprotodontidae sounds (true relative pack) kept; pelt drop resolves to own-named Diprotodon Skin variants')


FIX = {'aepyornis': aepyornis, 'doedicurus': doedicurus, 'arctodus': arctodus, 'megatherium': megatherium, 'hippopotamus_lemerlei': hippopotamus_lemerlei, 'camelops': camelops, 'macrauchenia': macrauchenia, 'toxodon': toxodon, 'cryptoprocta': cryptoprocta, 'diprotodon': diprotodon}
