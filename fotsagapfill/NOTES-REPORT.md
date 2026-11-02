# FotSA gap-fill REPORT

CURRENT (2026-11-01): 0.2.0 is the live version: `staging/fotsagapfill-0.2.0.zip`, installed standalone as Mods\fotsagapfill-0.2.0.zip (UNCONFIRMED: Mods copy 2,461,174 B differs from staging 2,441,434 B; Nick to confirm). The 0.1.0 text below is SUPERSEDED by the 0.2.0 section near the end (Diprotodon is BUILT, donor zygomaturustrilobus).

[SUPERSEDED 2026-11-01] Original 0.1.0 note: staged only: `staging/fotsagapfill-0.1.0.zip` (modid fotsagapfill). Nothing copied to Mods at the time; game not launched.

## (a) Existence check (15 species)

| Species | Status | Tier | Reason / note |
|---|---|---|---|
| Genyornis newtoni | PRESENT | - | In FotSA-Casuariidae dromornithidae. Dropped, not remodeled. |
| Thylacoleo carnifex | PRESENT | - | In FotSA-Vombatidae thylacoleonidae. Dropped, not remodeled. |
| Aepyornis | BUILT | 1 | donor FotSA-Dinornithidae / dinornisrobustus |
| Thambetochen | BUILT | 1 | donor FotSA-Dinornithidae / cnemiorniscalcitrans |
| Diprotodon | BUILT | 1 | donor FotSA-Vombatidae / zygomaturustrilobus (Diprotodon absent from installed packs; only Zygomaturus trilobus present) |
| Elasmotherium | BUILT | 1 | donor FotSA-Rhinocerotidae / coelodontaantiquitatis |
| Cryptoprocta | BUILT | 1 | donor FotSA-Viverridae / viverrazibetha |
| Megatherium | BUILT | 2 | donor FotSA-Vombatidae / zygomaturustrilobus |
| Doedicurus | BUILT | 2 | donor FotSA-Meiolaniidae / ninjemysoweni |
| Macrauchenia | BUILT | 2 | donor FotSA-Capreolinae / blastocerusdichotomus |
| Camelops | BUILT | 2 | donor FotSA-Capreolinae / cervalcesscotti |
| Toxodon | BUILT | 2 | donor FotSA-Bovinae / bubalusbrevicornis |
| Hippopotamus lemerlei | BUILT | 2 | donor FotSA-Bovinae / bubalusmindorensis |
| Arctodus | BUILT | 2 | own domain `fotsagapfill`, derived from vanilla bear-adult (0.2.0; was Pantherinae atrox in 0.1.0) |
| Procoptodon | NOT BUILT | 2 | Hopping bipedal short-faced kangaroo: no matching hopping/bipedal rig in any installed pack; a quadruped clone would be incoherent with its anims and ai. |

Not on the list but already installed: Coelodonta antiquitatis (Rhinocerotidae), Mammuthus (Elephantidae).

## (b) Built species

### aepyornis (tier 1) new type `aepyornismaximus`
- Donor: FotSA-Dinornithidae / `dinornisrobustus`. 
- Spawn/realm: eastern afrotropic; home Madagascar [-26,-12]x[43,51]; climate {'minTemp': 18, 'maxTemp': 34, 'minRain': 0.1, 'maxRain': 0.6, 'minForestOrShrubs': 0.05, 'maxForest': 0.5, 'maxShrubs': 1.0}
- Remodel: 4 shape ops; fields {'weightByType': {'female': 480, 'male': 340}, 'sizeByType': {'female': 1.0, 'male': 0.88}}; disabled behaviors []; recolor [{'dh': -18, 'ms': 0.75, 'mv': 0.92}, {'only_hue': (0, 60), 'mv': 1.05}]
- Texture: Madagascar spiny-forest/dry scrub: warm sandy-brown plumage, desaturated, slightly lighter than the South Island moa.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-1.44, 0.12, -0.11] max [1.59, 2.38, 1.11]

### thambetochen (tier 1) new type `thambetochenchauliodous`
- Donor: FotSA-Dinornithidae / `cnemiorniscalcitrans`. 
- Spawn/realm: oceanic; home Hawaii [18,23]x[-162,-154]; climate {'minTemp': 18, 'maxTemp': 30, 'minRain': 0.4, 'maxRain': 1.0, 'minForestOrShrubs': 0.1, 'maxForest': 1.0, 'maxShrubs': 1.0}
- Remodel: 4 shape ops; fields {'weightByType': {'*': 22}, 'sizeByType': {'female': 1.05, 'male': 1.1}}; disabled behaviors []; recolor [{'dh': -4, 'ms': 1.35, 'mv': 0.78}, {'only_hue': (0, 40), 'dh': 14, 'ms': 0.8}]
- Texture: Hawaiian lava-forest island plumage: dark brown-grey with an olive tone.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [0.03, 0.01, 0.27] max [1.08, 1.08, 0.74]

### diprotodon (tier 1) new type `diprotodonoptatum`
- Donor: FotSA-Vombatidae / `zygomaturustrilobus`. 
- Spawn/realm: australasian; home inland Australia [-44,-10]x[112,154]; climate {'minTemp': 12, 'maxTemp': 36, 'minRain': 0.1, 'maxRain': 0.55, 'minForest': 0.0, 'maxForest': 0.35, 'maxShrubs': 1.0}
- Remodel: 8 shape ops; fields {'weightByType': {'female': 2300, 'male': 2900}}; disabled behaviors []; recolor [{'dh': -4, 'ms': 0.7, 'mv': 1.12}, {'only_hue': (20, 60), 'dh': -6, 'ms': 0.9, 'mv': 1.0}]
- Texture: Arid inland plains: grey-brown to ochre-brown coat, desaturated and lighter than the forest-dwelling Zygomaturus.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-0.83, -0.0, -0.03] max [1.56, 1.86, 1.04]

### elasmotherium (tier 1) new type `elasmotheriumsibiricum`
- Donor: FotSA-Rhinocerotidae / `coelodontaantiquitatis`. 
- Spawn/realm: central palearctic; home Eurasian steppe [40,60]x[45,100]; climate {'minTemp': -8, 'maxTemp': 14, 'minRain': 0.1, 'maxRain': 0.5, 'minForestOrShrubs': 0.0, 'maxForest': 0.25, 'maxShrubs': 0.6}
- Remodel: 6 shape ops; fields {'weightByType': {'female': 3500, 'male': 4300}}; disabled behaviors ['antlergrowth']; recolor [{'dh': -18, 'ms': 0.55, 'mv': 1.5}]
- Texture: Cold dry steppe: pale buff-grey coat, markedly lighter and less olive than the woolly rhino.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-1.61, 0.0, -0.11] max [2.02, 2.53, 1.12]

### cryptoprocta (tier 1) new type `cryptoproctaspelea`
- Donor: FotSA-Viverridae / `viverrazibetha`. 
- Spawn/realm: eastern afrotropic; home Madagascar [-26,-12]x[43,51]; climate {'minTemp': 18, 'maxTemp': 38, 'minRain': 0.25, 'maxRain': 0.75, 'minForest': 0.2, 'maxForest': 0.9, 'maxShrubs': 1.0}
- Remodel: 7 shape ops; fields {'weightByType': {'*': 20}}; disabled behaviors []; recolor [{'dh': -26, 'ms': 2.3, 'mv': 0.65, 'av': 0.22}, {'rect': (5, 7, 9, 20), 'mv': 0.85}]
- Texture: Madagascar dry forest: uniform tawny reddish-brown (contrast compressed, no civet bands), slightly darker back.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-0.06, 0.01, 0.34] max [1.58, 0.57, 0.66]

### megatherium (tier 2) new type `megatheriumamericanum`
- Donor: FotSA-Vombatidae / `zygomaturustrilobus`. diprotodontidae rig: heavy plantigrade quadruped with clawed 5-finger hands/feet and a tail chain; walk/run/graze-free set matches a slow giant herbivore.
- Spawn/realm: atlantic neotropic; home Pampas/Gran Chaco [-40,-20]x[-66,-52]; climate {'minTemp': 6, 'maxTemp': 28, 'minRain': 0.2, 'maxRain': 0.7, 'minForest': 0.0, 'maxForest': 0.4, 'maxShrubs': 1.0}
- Remodel: 8 shape ops; fields {'weightByType': {'female': 3600, 'male': 4400}}; disabled behaviors []; recolor [{'dh': -4, 'ms': 0.8, 'mv': 1.3}]
- Texture: Pampas grassland: shaggy ochre-brown coat, warmer and lighter than the forest Zygomaturus.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-0.81, -0.01, -0.07] max [1.69, 1.71, 1.1]

### doedicurus (tier 2) new type `doedicurusclavicaudatus`
- Donor: FotSA-Meiolaniidae / `ninjemysoweni`. ninjemysoweni: only armoured-shell quadruped walker with a spiked tail club; walk/swim/threat/idle set fits a slow glyptodont. Egg-laying breeding retained (flagged).
- Spawn/realm: atlantic neotropic; home Pampas [-40,-28]x[-66,-55]; climate {'minTemp': 8, 'maxTemp': 28, 'minRain': 0.25, 'maxRain': 0.7, 'minForest': 0.0, 'maxForest': 0.35, 'maxShrubs': 1.0}
- Remodel: 7 shape ops; fields {'weightByType': {'female': 1400, 'male': 1800}}; disabled behaviors []; recolor [{'dh': 2, 'ms': 0.85, 'mv': 1.4}]
- Texture: Pampas grassland: sandy grey-tan carapace, lighter and warmer than the dark-olive Ninjemys.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-0.37, -0.0, 0.03] max [2.04, 1.01, 0.97]

### macrauchenia (tier 2) new type `macraucheniapatachonica`
- Donor: FotSA-Capreolinae / `blastocerusdichotomus`. blastocerusdichotomus (marsh deer, own shape): long-legged South American grazer rig with walk/trot/canter/gallop, same continent as Macrauchenia; antlers disabled.
- Spawn/realm: atlantic neotropic; home Pampas/Patagonian steppe [-52,-30]x[-72,-56]; climate {'minTemp': -2, 'maxTemp': 24, 'minRain': 0.12, 'maxRain': 0.55, 'minForest': 0.0, 'maxForest': 0.3, 'maxShrubs': 0.8}
- Remodel: 4 shape ops; fields {'weightByType': {'female': 900, 'male': 1100}}; disabled behaviors ['antlergrowth']; recolor [{'dh': 4, 'ms': 0.55, 'mv': 1.1}]
- Texture: Patagonian steppe/pampas: pale sandy grey-tan coat, much less rufous than the marsh deer.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-0.93, -0.01, 0.2] max [1.26, 2.11, 0.8]

### camelops (tier 2) new type `camelopshesternus`
- Donor: FotSA-Capreolinae / `cervalcesscotti`. cervalcesscotti (stag-moose, own shape): tall long-legged North American Pleistocene browser with a shoulder Hump element; same walk/trot/canter set; antlers disabled, hump enlarged.
- Spawn/realm: pacific nearctic; home arid western North America [28,42]x[-122,-100]; climate {'minTemp': 2, 'maxTemp': 36, 'minRain': 0.05, 'maxRain': 0.35, 'minForest': 0.0, 'maxForest': 0.2, 'maxShrubs': 1.0}
- Remodel: 6 shape ops; fields {'weightByType': {'female': 900, 'male': 1100}}; disabled behaviors ['antlergrowth']; recolor [{'dh': 14, 'ms': 0.95, 'mv': 2.1}]
- Texture: Arid west (desert scrub/grass): sandy buff coat, far lighter than the dark brown moose.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-1.16, -0.01, 0.08] max [1.48, 2.43, 0.92]

### toxodon (tier 2) new type `toxodonplatensis`
- Donor: FotSA-Bovinae / `bubalusbrevicornis`. bubalusbrevicornis (own 76x84 shape, 29 anims incl. jump/stepup/turn): heaviest humped bovine rig, plain walk/trot/canter/charge quadruped; horns come only from antlergrowth so they are disabled.
- Spawn/realm: atlantic neotropic; home Pampas and Gran Chaco [-40,-10]x[-66,-40]; climate {'minTemp': 8, 'maxTemp': 32, 'minRain': 0.3, 'maxRain': 0.85, 'minForest': 0.0, 'maxForest': 0.45, 'maxShrubs': 1.0}
- Remodel: 3 shape ops; fields {'weightByType': {'female': 1400, 'male': 1700}}; disabled behaviors ['antlergrowth']; recolor [{'dh': -6, 'ms': 0.6, 'mv': 0.85}]
- Texture: Humid pampas/wetland margins: dark grey-brown hide, desaturated and darker than the tan Chinese water buffalo.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-1.05, -0.01, 0.07] max [1.44, 1.45, 0.94]

### hippopotamus_lemerlei (tier 2) new type `hippopotamuslemerlei`
- Donor: FotSA-Bovinae / `bubalusmindorensis`. bubalusmindorensis (tamaraw, own 52x60 shape): stockiest, shortest-bodied bovine rig with swim anim and getoutofwater task; horns disabled via antlergrowth. Donor has no real water affinity: keeps donor swim/wander/getoutofwater behavior (no wallowing or submerged behavior).
- Spawn/realm: eastern afrotropic; home Madagascar [-26,-12]x[43,51]; climate {'minTemp': 16, 'maxTemp': 36, 'minRain': 0.3, 'maxRain': 0.9, 'minForest': 0.0, 'maxForest': 0.8, 'maxShrubs': 1.0}
- Remodel: 8 shape ops; fields {'weightByType': {'female': 420, 'male': 520}}; disabled behaviors ['antlergrowth']; recolor [{'dh': -8, 'ms': 0.6, 'mv': 1.35}]
- Texture: Madagascan wetlands/riverine forest: slate grey-brown hide, lighter and greyer than the dark tamaraw.
- Validation: testzip OK; JSON parse failures 0; patch path failures 0 of 1318; unresolved refs none; texture dims MATCH donor; VsShapeCheck 0 error, 0 warn (clean); bbox min [-0.52, 0.0, 0.23] max [1.17, 0.9, 0.77]

### arctodus (tier 2) entity `fotsagapfill:arctodus` variant `simus` (0.2.0)
- Donor: vanilla `game:bear-adult` (brown type as base), loaded read-only from the game install; new entity in the fotsagapfill domain, not a patch of the vanilla entity. No Pantherinae patches, lion taxidermy, cub or pelt references remain (zip has no pantherinae assets).
- Kept from vanilla: shape and animations incl. Stand, 15 ai tasks, `game:creature/bear/*` sounds, drops `game:bushmeat-raw` / `game:hide-raw-huge` / `game:fat`. Health on client and server; vanilla bear has no gait behavior, so none added. Adult only: vanilla bear has no baby or breeding (known limit).
- Remodel inside the vanilla skeleton (element names kept so all anims bind): limbs y x1.28, mouth z x0.72, torso +9 voxels, Stand lift +4.49 voxels; shoulder height 1.60 blocks (F) / 1.77 (M); weight 600 / 800 kept; collision, selection and dead boxes set.
- Spawn/realm: pacific nearctic, atlantic nearctic; home N. America [32,65]x[-135,-80]; climate unchanged (minTemp -8, maxTemp 20, minRain 0.2, maxRain 0.7, maxForest 0.8, maxShrubs 1.0).
- Texture: brown recoloured to dark chestnut, 3 variants 256x304, same dims as vanilla. Real coat colour is unknown (inferred).
- Validation (0.2.0): VsShapeCheck 0 error 0 warn on 13 anims; groundcheck PASS idle -0.004, walk -0.006 (donor bear -0.060); Stand -0.187 (donor -0.182); run -0.122 (donor -0.066, outside the idle/walk criterion, not adjusted).

## (c) Tier 2 flags

- megatherium: shares the Zygomaturus rig with Diprotodon; claws/arms/tail only distinguish it. Quadrupedal wombat-gait body for a sloth.
- doedicurus: donor lays eggs (seekblockandlay, multiply disabled) retained; sprawling reptile leg posture; baby shape still shows horns.
- macrauchenia / camelops: cervid rig with antlers disabled via antlergrowth (client+server); long neck is a scaled donor neck, anims unchanged.
- toxodon / hippopotamus_lemerlei: bovine rig, horns disabled. Hippo donor has no water affinity; kept donor swim/wander/getoutofwater only, no wallowing or submerged behavior.
- arctodus (0.2.0): vanilla bear rig and anims, adult only (no vanilla baby/breeding); hunting style disputed; coat colour unknown; Stand anim and 13 anims verified at file level only, in-game look UNVERIFIED.
- All: sounds, drops, items cloned from donor; gait/health behaviors inherited on both client and server since entity files are patched in place.
- aepyornis bbox y-min 0.12 (feet slightly above ground in static pose; inherited donor stance); not adjusted.

## (d) Deviations

- thambetochen donor changed to cnemiorniscalcitrans because gracilis has no own shape.
- elasmotherium nasal horns disabled via antlergrowth, plus a grafted forehead horn.
- lang: English only, no fr/uk.
- elasmotherium horn drops untouched (donor horn items).
- Hitboxes, sizes, weights are estimates.
- Procoptodon not built (see a).

## (e) UNVERIFIED

- In-game look, spawn behavior, patch application at game load (no launch allowed).
- Biomes core realm patches (dependsOn biomes) not exercised.


## Fact-based fix pass (0.2.0)

Zip: `staging/fotsagapfill-0.2.0.zip` (modinfo 0.2.0, staged only, not installed). The 0.1.0 zip is untouched. Sections above that describe donor choices for 0.1.0 are superseded by this table where they differ. Confidence: evidence = documented fact or game value; inferred = reasoned from anatomy or relatives; unknown = no source. In-game look of every change is UNVERIFIED (file-level checks only; game not launched). Groundcheck = lowest y over frames, model space, pass about -0.05..+0.05 or inside the donor's own range.

| # | Species | Fact | Confidence | Change | Validation | Flags |
|---|---------|------|------------|--------|------------|-------|
| 1 | aepyornis | flightless ratite, no live birth; hatched from giant eggs | evidence (ratite), inferred (size) | own chick shape and texture, female 3.0 blocks, male 2.64, hitboxes 2.1x2.9 / 1.85x2.55; kiwi idle call; pelt item already named Elephant Bird Skin | groundcheck idle 0.000, walk -0.062 (donor -0.064), baby PASS | PLACEHOLDER: cassowary grunt for hurt/death (no ratite elephant bird sound exists) |
| 2 | doedicurus | glyptodont, a placental mammal: live birth, no eggs | evidence | live birth on this variant only (egg-laying task, egg entity/item/lang/nest removed for the type), pregnancy 56 days, calf (was hatchling) remodelled with adult ops, Walk/Swim limb swing x0.25 | groundcheck idle 0.000, walk -0.045 (donor -0.033), baby PASS, VsShapeCheck 0/0 | PLACEHOLDER: generic hooved sniff/call (no xenarthran pack); `attributes.eggTypes` left (unused) |
| 3 | arctodus | tremarctine bear, long-legged, highly carnivorous, hunting style disputed | evidence (bear, legs), unknown (coat, hunting) | new entity `fotsagapfill:arctodus` from vanilla bear-adult: vanilla anims incl. Stand, 15 ai tasks, `game:creature/bear/*` sounds, limbs x1.28, mouth x0.72, shoulder 1.60 / 1.77, dark chestnut | VsShapeCheck 0/0 on 13 anims, groundcheck idle -0.004, walk -0.006 (donor -0.060), Stand -0.187 (donor -0.182) | NOT DONE: baby and breeding (vanilla bear has none); run -0.122 vs bear -0.066 not adjusted; coat colour unknown |
| 4 | megatherium | mainly quadruped, could stand upright to browse, walked on foot sides (claws), browser | evidence | own Stand animation (rear-up, tail as tripod) triggered by a variant-only idle task (6 s, cooldown 90-420 s), hind thigh y +27 pct, Tail2 x1.4, Walk foot roll 10 deg, Walk/Run front dip fixed; cub = adult remodel | VsShapeCheck 0/0 adult+baby, whole-anim min y -0.022, stand hold -0.014; groundcheck walk -0.022 (donor -0.037), run -0.040 (donor -0.151) | PLACEHOLDER: generic hooved sounds; UNVERIFIED: Stand look, tail curl, foot roll; Stand timing is my choice |
| 5 | hippopotamus_lemerlei | mostly riparian, less aquatic than H. amphibius, browser | evidence (habitat), inferred (behaviour) | spawn climate minForest 0.15, minRain 0.45 (VS has no near-water spawn condition); buffalo sounds removed; calf = adult remodel with sheep idle replaced; Rear bob raised; swim and getoutofwater kept, no flop or dive | groundcheck idle +0.001, walk -0.034 (donor -0.030), run -0.038 (was -0.083), baby PASS | PLACEHOLDER: calf idle = generic hooved sniff; adult SILENT because no hippo sounds are installed; spawn has no water tie |
| 6 | camelops | pacing gait inferred from tracks and anatomy; hump unproven (Webb 1965 argued one); mixed browser | inferred (gait), unknown (hump) | pacing walk: both hind legs retimed 22 of 80 frames, hoof-x phase LF-LH -0.28 -> +0.85, RF-RH -0.28 -> +0.91; Haunch lift to keep hooves grounded; Trot already diagonal, unchanged; own calf shape and pelt clone, moose and sheep sounds replaced, Fawn -> Calf labels; hump kept | groundcheck idle -0.000, walk -0.032 (donor -0.059), PASS adult+baby, 0 err 0 warn | PLACEHOLDER: generic hooved sounds (no camelid pack); judgement call: hump kept; pre-existing detached tiny Wattle element; calf hitbox from donor ratio |
| 7 | macrauchenia | long neck held erect at rest, level when running; moose-like nose favoured over a trunk | inferred | nose kept, no trunk; Neck +10..30 deg and Head -4..-12 deg on Trot/Canter/Stot/Run/Charge on own shape; head-minus-chest dy idle 0.76, trot 0.63, canter 0.56, run 0.20; own calf shape and pelt clone (white-tailed fawn removed), deer and sheep sounds replaced, Fawn -> Calf | groundcheck idle -0.004, walk -0.041 (donor -0.048), run -0.050 (donor -0.057), baby PASS | PLACEHOLDER: generic hooved sounds (no litoptern pack) |
| 8 | toxodon | notoungulate, not a bovid; horns absent | evidence | own calf shape and pelt clone (buffalo calf rig + adult remodel minus Hump); buffalo moo/idle and sheep idle replaced; horns stay off | groundcheck idle +0.000, walk -0.011 (donor -0.026), charge -0.050 (donor -0.064), baby PASS | PLACEHOLDER: generic hooved call/sniff for adult and calf (adult is not silent here: the generic sound suits) |
| 9 | thambetochen | flightless moa-nalo, an anatid (duck relative) | evidence | none needed: goose-call pack is a true relative, pelt labelled Moa-nalo Plumage/Skin, drop is own-named variant | groundcheck idle +0.015, walk -0.035 (donor -0.056), baby PASS | calf is the donor chick shape unchanged; nest shape is the shared generic nest |
| 10 | diprotodon | giant diprotodontid marsupial | evidence | sounds are the vombatidae-pack diprotodontidae bellow/snort/babycall (true relative); Walk/Run root offsetY corrected per frame to the donor curve | groundcheck walk -0.079 -> -0.037 (donor -0.037), run -0.331 -> -0.166 (donor -0.163; donor itself sinks), idle -0.002, baby PASS | none |
| 11 | elasmotherium | rhinocerotid | evidence | none needed: rhinocerotidae roar/idlesnort are a true relative, pelts and shapes already own-named | groundcheck idle +0.004, walk -0.013 (donor -0.047), baby PASS | none |
| 12 | cryptoprocta | fossa-like euplerid feliform, not a civet | inferred | Walk Hip bob +0.4 voxel so legs no longer dip; pelt already "Giant Fossa Pelt" | groundcheck walk -0.055 -> -0.031 (donor -0.034), idle +0.006, baby PASS | PLACEHOLDER: viverridae idle* sound kept as nearest installed feliform (no Eupleridae pack) |

Final validation (`work/validate2.py`, `work/groundcheck.py`):
- zipfile.testzip OK, 241 files; JSON parse failures 0; patch path failures 0 of 1082; unresolved entity refs none; texture dims MATCH donor for every cloned texture; texture paths missing 0; 26 PNGs, 0 bad.
- VsShapeCheck on 22 entity shapes plus arctodus: 0 error, 0 warn. Groundcheck: 0 fails of 23 shapes.
- Donor entities of Vombatidae, Bovinae and Capreolinae carry health on the server only and no gait behavior, same as vanilla; left unchanged.
- Worldgen and spawn changes only affect newly generated chunks.
