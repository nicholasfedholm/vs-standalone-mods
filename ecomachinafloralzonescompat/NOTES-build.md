# Eco Machina × Floral Zones compatibility patch

Date: 2026-10-19 · Game: Vintage Story 1.22.7 · **Nothing was installed by the build session (2026-10-19). UNCONFIRMED: Mods (2026-11-01) has EcoMachinaFloralZonesCompat_v1.0.0.zip (2,574 B, 2026-10-20 18:44), vsecomachina_0.6.1.zip (10-19 18:24) and all 8 FloralZones packs; Nick to confirm the install.**

Deliverable: **`EcoMachinaFloralZonesCompat_v1.0.0.zip`** (modid `ecomachinafloralzones`, content mod, JSON patches only, no C#)
SHA-256 `f547e237d762ed84eb19c5989439c7f3d7860948ba3315fca1573e2bccc51351`

## Short answer

- **All 18 new-wood species are picked up by Eco Machina 0.6.1 without any patch.** Every trunk is recognised (`log-grown-*` / `logsection-grown-*`), counts as a "generated" log for auto-claim, and gets a clean bark/end-grain texture split. Every resin, sap and section block maps back to an existing `log-grown` twin. No textures are missing. Trunk shaping needed **0 patches, and 0 C#**.
- **The only gap is the canopy on 4 Cape treegens (3 species) and Circumboreal `piceaglaucasmall`.** They generate `-placed-` leaves, which Eco Machina rejects, so they get no foliage stubs or branch tint. Worldgen preclaim also skips them (details below).
- **Cape decision: the `-placed-` leaves are accidental, so I changed them, but not with a plain rename.** In the Cape leaf blocktypes the author swapped the vanilla `grown`/`placed` names, and only `placed*` decays. The patch points the worldgen treegens at `grown` *and* gives Cape `grown` leaves the same decay behaviour. Felled Cape trees still drop their canopy. See [Cape decision](#cape-decision).
- **Circumboreal `piceaglaucasmall` is a plain bug.** This pack uses vanilla semantics, so its `-placed-` leaves never decayed. Switching to `-grown-` fixes both Eco Machina and leaf decay.
- **Total: 3 patch files, 14 operations.** That's 5 treegens (10 replaces) and 2 Cape leaf blocktypes (2 replaces and 2 adds).
- **Not tested in game yet.** This is a static check against decompiled Eco Machina 0.6.1 and the game's own TreeGen, BlockLeaves and LeafBlockDecay code, plus a simulated patch application. Run the [test plan](#test-plan-in-game) before trusting it.

## Folder layout

| Path | What |
|---|---|
| `EcoMachinaFloralZonesCompat_v1.0.0.zip` | The patch mod. It's the only thing to install |
| `patch/` | Unzipped source of the same mod (`modinfo.json` and `assets/ecomachinafloralzones/patches/*.json`) |
| `orig/` | Fresh Mod DB downloads (Eco Machina 0.6.1 and the 8 Floral Zones packs), plus `releases.json` with versions, tags and SHA-256 |
| `x/` | Extracted copies of the `orig/` zips, used for analysis |
| `tools/verify_species.py` | Static check that mirrors Eco Machina's classifier and texture rules per treegen (`--patched` applies our patches first). Output: `tools/verify_orig.json` and `tools/verify_patched.json` |
| `tools/apply_check.py` | Applies the patches to the real target files and checks the result (only the intended keys change, decay semantics are right) |
| `tools/j5.py` | Lenient JSON5 loader for VS assets |
| `fetch.py` | The download script |

## Downloads (step 1–2)

| Mod | Version | File | Mod DB tags |
|---|---|---|---|
| Eco Machina | 0.6.1 | vsecomachina_0.6.1.zip | 1.22.0, 1.22.1, 1.22.2 (**not tagged 1.22.7**; modinfo needs game ≥ 1.22.0, so it will load) |
| Floral Zones: Cape Region | 1.0.38 | FloralZonesCapeRegion-v1.0.38.zip | 1.22.7 |
| Floral Zones: Caribbean Region | 1.0.30 | FloralZonesCaribbeanRegion-v1.0.30.zip | 1.22.7 |
| Floral Zones: Central Australian Region | 1.0.28 | FloralZonesCentralAustralianRegion-v1.0.28.zip | 1.22.7 |
| Floral Zones: Circumboreal Region | 1.0.4 | FloralZonesCircumborealRegion-v1.0.4.zip | 1.22.7 |
| Floral Zones: Cosmopolitan Region | 1.0.14 | FloralZonesCosmopolitanRegion-v1.0.14.zip | 1.22.7 |
| Floral Zones: East Asiatic Region | 1.0.25 | FloralZonesEastAsiaticRegion-v1.0.25.zip | 1.22.7 |
| Floral Zones: Mediterranean Region | 1.0.25 | FloralZonesMediterraneanRegion-v1.0.25.zip | 1.22.7 |
| Floral Zones: Neozeylandic Region | 1.0.26 | FloralZonesNeozeylandicRegion-v1.0.26.zip | 1.22.7 |

These are the same versions and byte sizes as in the 2026-10-18 audit.

## What changed (patch contents)

Every operation has `dependsOn: [<that Floral Zones pack>, vsecomachina]`, so nothing is patched unless both are loaded. The game ANDs the `dependsOn` entries (`ModJsonPatchLoader`). `modinfo.json` only requires `game ≥ 1.22.0`, so you can install it with any subset of the packs.

| File | Target | Op | Change |
|---|---|---|---|
| `cape-treegen-grown-leaves.json` | `game:worldgen/treegen/afrocarpusfalcatus.json`, `…afrocarpusfalcatuslarge.json`, `…ocoteabullata.json`, `…searsialancea.json` | replace ×8 | `/treeBlocks/leavesBlockCode` and `/treeBlocks/leavesBranchyBlockCode`: `…leaves(branchy)-placed-<wood>` → `…leaves(branchy)-grown-<wood>` |
| `circumboreal-piceaglaucasmall-grown-leaves.json` | `game:worldgen/treegen/piceaglaucasmall.json` | replace ×2 | Same, `-placed-piceaglauca` → `-grown-piceaglauca` (same codes as the big `piceaglauca` treegen) |
| `cape-leaves-grown-decay.json` | `floralzonescaperegion:blocktypes/plant/leaves/normal.json` and `…/branchy.json` | replace ×2, add ×2 | `behaviorsByType` is rewritten as `{"*-placed*-*": [decay, RainDrip], "*-grown-*": [decay, RainDrip], "*": [RainDrip]}`. I replaced the whole object so `*-grown-*` sits before the `*` catch-all, because ByType resolution takes the first match. `attributes/canDecayByType/*-grown-*` is set to `true`. `placed*` keeps its existing behaviour |

`tools/apply_check.py` result: every op hits an existing path. Only `leavesBlockCode` and `leavesBranchyBlockCode` change in the 5 treegens. Only `behaviorsByType` and `canDecayByType` change in the 2 blocktypes. `placed`/`placed1-7` behaviour is unchanged, and `grown` gains `PushEventOnBlockBroken(testForDecay)` and `canDecay=true`. **PASS.**

## Per-species table (18 new-wood log trees)

The trunk checks hold for all 18, both before and after the patch:
- Eco Machina classifies the block as Wood: `log-` / `logsection-` prefix, not `lognarrow-`, `bamboo-` or `-placed-`.
- `IsGeneratedTreeLog` is true (`type=grown`).
- The `-ud` texture set splits 4/2: `all` gives bark (`<pack>:block/wood/bark/<wood>`) and `up`/`down` give end grain (`<pack>:block/wood/treetrunk/<wood>`). That's the grouped-fingerprint path, not legacy.
- The `-ns`/`-we` variants exist, and all bark, end-grain and `inside-*` debarked textures exist on disk.
- Resin logs (`log-resin-<wood>-ud`, including the Central Australian **sap** log, which also uses `log-resin-*` codes) have `resinbark1/2` textures. If the resin overlay fails, Eco Machina falls back to `log-grown-<wood>-ud` (`ModResinLogSubstitution`).
- `logsection-grown-<wood>-{ne,se,sw,nw}-ud` maps to `log-grown-<wood>-ud` for connector textures.

| # | Pack | Species (wood code) | Treegens | Extra trunk blocks | Worldgen leaves before | Eco Machina foliage before | After patch |
|---|---|---|---|---|---|---|---|
| 1 | Cape | Afrocarpus falcatus, Outeniqua yellowwood (`afrocarpusfalcatus`) | `afrocarpusfalcatus`, `afrocarpusfalcatuslarge` | logsection + resin | all `placed` | **no** | yes (**patched**) |
| 2 | Cape | Ocotea bullata, stinkwood (`ocoteabullata`) | `ocoteabullata` | – | all `placed` | **no** | yes (**patched**) |
| 3 | Cape | Searsia lancea, karee (`searsialancea`) | `searsialancea` | – | all `placed` | **no** | yes (**patched**) |
| 4 | Caribbean | Lysiloma latisiliquum (`lysilomalatisiliquum`) | `lysilomalatisiliquum` | – | `grown` | yes | yes (no change) |
| 5 | Central Australian | Corymbia aparrerinja, ghost gum (`corymbiaaparrerinja`) | `corymbiaaparrerinja`, `corymbiaaparrerinjacrooked` | sap (`log-resin-*`) | `grown` | yes | yes (no change) |
| 6 | Central Australian | Eucalyptus camaldulensis, river red gum (`eucalyptuscamaldulensis`) | `eucalyptuscamaldulensis`, `eucalyptuscamaldulensislarge` | resin | `grown` | yes | yes (no change) |
| 7 | Circumboreal | Abies balsamea, balsam fir (`abiesbalsamea`) | `abiesbalsamea` | resin | `grown` | yes | yes (no change) |
| 8 | Circumboreal | Alnus glutinosa, black alder (`alnusglutinosa`) | `alnusglutinosa` | – | `grown` | yes | yes (no change) |
| 9 | Circumboreal | Larix laricina, tamarack (`larixlaricina`) | `larixlaricina` | – | `grown` | yes | yes (no change) |
| 10 | Circumboreal | Picea glauca, white spruce (`piceaglauca`) | `piceaglauca`, `piceaglaucasmall` | – | `grown`; **`placed` in `piceaglaucasmall`** | yes / **no (small)** | yes (**small patched**) |
| 11 | Circumboreal | Pinus sibirica, Siberian pine (`pinussibirica`) | `pinussibirica` | resin | `grown` | yes | yes (no change) |
| 12 | Circumboreal | Quercus petraea, sessile oak (`quercuspetraea`) | `quercuspetraea` | – | `grown` | yes | yes (no change) |
| 13 | Mediterranean | Populus alba, white poplar (`populusalba`) | `populusalba`, `oldpopulusalba` | – | `grown` | yes | yes (no change) |
| 14 | Mediterranean | Taxus baccata, yew (`taxusbaccata`) | `taxusbaccata`, `oldtaxusbaccata` | – | `grown` | yes | yes (no change) |
| 15 | Neozeylandic | Araucaria heterophylla, Norfolk Island pine (`araucariaheterophylla`) | `araucariaheterophylla`, `araucariaheterophyllalarge` | logsection | `grown` | yes | yes (no change) |
| 16 | Neozeylandic | Dacrydium cupressinum, rimu (`dacrydiumcupressinum`) | `dacrydiumcupressinum`, `…medium`, `…small` | logsection + resin | `grown` | yes | yes (no change) |
| 17 | Neozeylandic | Nothofagus menziesii, silver beech (`nothofagusmenziesii`) | `nothofagusmenziesii`, `nothofagusmenziesiilarge` | logsection | `grown` | yes | yes (no change) |
| 18 | Neozeylandic | Podocarpus totara, tōtara (`podocarpustotara`) | `podocarpustotara`, `podocarpustotaralarge` | logsection | `grown` | yes | yes (no change) |

The verifier found **18 species / 29 treegens**, matching the audit (Cape 4, Caribbean 1, Central Australian 4, Circumboreal 7, Mediterranean 4, Neozeylandic 9). Before the patch, 5 treegens had problems, all `-placed-` leaves. After, **0**.

The 15 vanilla-log species (Caribbean 5, Central Australian 2, East Asiatic 6, Mediterranean 2) use vanilla `game:log-grown-*` trunks. Their custom FZ leaves are all `-grown-`, so they need no patch.

### What the `-placed-` gap actually did (beyond "no foliage")

Reading Eco Machina's claim code turned up one more effect the audit didn't cover:

- **Worldgen preclaim** (`WorldgenTreePreclaimServerSystem`, on by default) needs at least one leaf that passes `TryClassify`, and `-placed-` fails it. So Cape trees and small white spruces were **never preclaimed** at chunk generation.
- **Runtime auto-claim** (`VanillaTreeAutoClaimServerSystem`) still picks them up later. Its fallback leaf-evidence scan uses `IsTreeLeaves`, which doesn't check `-placed-`. So the trunks were tapered anyway, just later and with a 0-leaf tree graph (no stubs, no tint).

With the patch, these trees go through the same path as every other FZ tree.

## Cape decision

**Question:** did the Cape author use `-placed-` on purpose?

**Evidence:**
1. Vanilla 1.22.7 `leaves/normal.json` has type states `grown, grown1…grown7, placed`. `grown*` gets `PushEventOnBlockBroken(testForDecay)` and `canDecay=true`. `placed` is the non-decaying player variant.
2. Cape `leaves/normal.json` and `leaves/branchy.json` have `placed, placed1…placed7, grown`, with decay and the felling group on `placed*`. That's an **exact name swap** of the vanilla file, and Cape is the only pack with it. The other 7 packs, including the Circumboreal and Cosmopolitan leaves, use vanilla semantics.
3. The swap doesn't fit how the game works, which points to an accident rather than design:
   - `BlockLeaves.OnPickBlock` hard-codes `placed`. In Cape, middle-click-picked leaves therefore *decay* once placed.
   - The creative inventory also offers `placed` leaves, which decay.
   - `TreeGenBlocks.ResolveBlockNames` only builds leaf levels for codes whose second part is `grown`, so `placed1…placed7` are never used by worldgen. They're dead variants left over from the rename.
4. No comment explains it. The only comment in either file is the stock vanilla `__comment` about `BlockLeaves`. Nothing differs per species: all 5 Cape tree species, including the 2 narrow-trunk ones, use `-placed-` the same way.

**Conclusion:** it's accidental (a grown↔placed rename), not a deliberate per-species choice. **But a naive treegen switch is not safe.** Cape `grown` leaves don't decay, so Cape canopies would float forever after felling. That's why the patch also gives Cape `grown` the decay behaviour and `canDecay`. `placed*` keeps decaying, so trees in chunks generated before the patch still behave the same, and player-placed leaves behave exactly as they did before.

**Left alone on purpose:**
- The Cape narrow-trunk and shrub treegens (`leucadendronargenteum`, `pterocelastrustricuspidatus(large)`, `shrub*`). Eco Machina hard-excludes their `lognarrow-*` trunks anyway, so switching their leaves would gain nothing. They keep `-placed-`, and their leaves still decay.
- The Cape creative-inventory and pick-block quirk. It's an upstream FZ issue and has nothing to do with Eco Machina.

**Circumboreal `piceaglaucasmall`:** that pack uses vanilla semantics, so `-placed-` there meant the small white spruce's leaves **never decayed**. The big `piceaglauca` treegen uses `-grown-`. The switch fixes a bug and changes nothing else. Small spruces now also get the `grown1-7` leaf levels, the same as the big one.

## Not fixable / out of scope

- **Narrow trunks (`lognarrow-*`), bamboo and palms:** Eco Machina hard-excludes these (`ExcludedTreeFamilyPrefixes`). That would need a C# change to Eco Machina itself. The exclusion is intentional and these trees aren't in the 33-tree count.
- **Trees already generated:** treegen patches only affect **new chunks**. Cape and small-spruce trees in already-explored chunks keep `-placed-` leaves. Their trunks still get tapered through runtime auto-claim, but their canopies stay vanilla. A world without FZ chunks yet, or `/wgen regen` on a test world, avoids this.
- **Upstream FZ oddities I noticed but didn't touch:** the Neozeylandic zip ships a stray `assets/floralzonescaribbeanregion/` folder (baskets, heart of palm). The Cape `log.json` `WrenchOrientable` basecode points at `game:log-placed-{wood}`, which doesn't exist for FZ woods.

## Test plan (in game)

Use a **throwaway test world**, never Nick's main save.

### Setup
1. Install Eco Machina 0.6.1, all 8 FZ packs and `EcoMachinaFloralZonesCompat_v1.0.0.zip` (see [Install](#install-steps)).
2. Start the game once so `%APPDATA%\VintagestoryData\ModConfig\ecomachina.json` gets created, then quit. Set these keys:
   ```json
   "CubeRouteDiagEnabled": true,
   "VanillaAutoClaimDiagEnabled": true,
   "WorldgenPreclaimDiagEnabled": true
   ```
   Leave `EnableTaperedWoodRendering`, `EnableFoliageStubs`, `EnableBranchColorTinting`, `AutoClaimMode: "All"` and `EnableWorldgenPreclaim` at their defaults (true / All / true).
3. Create a **new** creative world and enter it. Then run `/time set day`.
4. In `%APPDATA%\VintagestoryData\Logs\server-main.log`, confirm the patches applied and none were skipped. Look for the JSON patch summary line (`… patches total, … successfully applied`). There must be **no** `Patch file ecomachinafloralzones:patches/…` errors or warnings.
   - With verbose debug logging, `server-debug.log` should **not** show `Unmet DependsOn condition` for our files. If it does, a pack or Eco Machina isn't loaded.
   - There must be no `Tree gen tree … No block found with the blockcode …` warnings for `afrocarpusfalcatus`, `ocoteabullata`, `searsialancea` or `piceaglaucasmall`.

### Per-tree procedure
For each row below:
1. Stand on open, flat ground and run the `/wgen tree` command. The treegen name tab-completes.
2. Walk around the tree and check the **trunk**: Eco Machina tapers it, round and narrowing towards the top with root flare. Vanilla is square, full-block logs.
3. Check the **canopy**: Eco Machina adds foliage stubs/tufts at branch tips and tints branch wood near the leaves. Vanilla is plain leaf cubes only.
4. Look at the tree and run `/em tree select` (needs root). That arms `[ClaimDiag]` for that tree.
5. Check `client-debug.log` for `[ModWoodResolve] block=<pack>:log-grown-<wood>-ud … uvMode=Fingerprint reason=…`. It's logged once per block per session, and there must be no `->legacy` or `hard fallback`.
6. Check `server-debug.log` for `[ClaimDiag] Build: … leavesCount=N branchyLeavesCount=M`. **N+M must be > 0.**

| Pack | Command | Expected trunk | Expected canopy | What it proves |
|---|---|---|---|---|
| Cape | `/wgen tree afrocarpusfalcatus 1 6` (also try `afrocarpusfalcatuslarge 1 8` for logsection + resin) | Eco Machina tapered | **Eco Machina stubs + tint** (vanilla before the patch) | Cape fix works. `leavesCount > 0` |
| Cape (decay) | Fell that tree: `/giveitem axe-felling-copper 1`, chop the trunk base, wait ~1 min | – | Leaves decay away and drop seeds/sticks, as they did before the patch | The decay patch on `grown` works |
| Caribbean | `/wgen tree lysilomalatisiliquum 1 6` | Eco Machina tapered | Eco Machina | Single-wood pack, no patch needed |
| Central Australian | `/wgen tree eucalyptuscamaldulensis 1 6` (plus `corymbiaaparrerinja 1 6` for the sap log) | Eco Machina tapered, resin/sap blocks tapered like their neighbours | Eco Machina | Resin/sap path. Check the log for `mod-resin-grown-fallback` (OK if present, it's the designed fallback) |
| Circumboreal | `/wgen tree piceaglaucasmall 1 6` and `/wgen tree quercuspetraea 1 6` | Eco Machina tapered | **Eco Machina on both** | Small-spruce fix + reference |
| Cosmopolitan | `/wgen tree rhizophoramangle 1 6` (mangrove; the pack has no log trees) | **Vanilla** (narrow trunk, excluded by design) | Vanilla | Excluded families stay untouched, no errors |
| East Asiatic | `/wgen tree quercusserrata 1 6` | Eco Machina tapered (vanilla oak log) | Eco Machina (custom FZ `-grown-` leaves) | Vanilla-log + custom-leaf trees work |
| Mediterranean | `/wgen tree populusalba 1 6` (also `oldtaxusbaccata 1 8`) | Eco Machina tapered | Eco Machina | |
| Neozeylandic | `/wgen tree dacrydiumcupressinum 1 6` (also `araucariaheterophyllalarge 1 8`) | Eco Machina tapered, sections and resin included | Eco Machina | logsection + resin in one pack |

Notes:
- `/wgen tree <name> [size] [aheadoffset]` uses the treegen file name. Bigger `size` values make bigger trees.
- If a trunk stays square, check `client-debug.log` for `[ModWoodResolve] … reason=` and `Render-only tapered wood: … falling back to vanilla`. Report the line. A failure there would need C#, because JSON can't fix it.
- If an Eco Machina canopy is missing only on Cape, check that the leaves under the crosshair are `…-grown-…`. Use the block info HUD (or `/giveblock floralzonescaperegion:leaves-grown-afrocarpusfalcatus 1` to compare codes). If they're `-placed-`, the patch didn't apply. Go back to setup step 4.
- **Natural-worldgen check (optional):** in a new survival-generation test world, fly to a matching climate. Cape is warm and dry-ish, Circumboreal is cold. Confirm naturally spawned trees look the same as the `/wgen` ones and that `[PreclaimDiag] … treesAdded=` counts go up in those chunks.
- **Pass criteria:** every row matches the expected trunk and canopy, the Cape decay check passes, and the logs have no patch errors and no `hard fallback` for FZ blocks.

## Install steps

After the texture fix finishes, and **only after the test plan passes on a test world**:
1. Close Vintage Story.
2. Copy into `%APPDATA%\VintagestoryData\Mods\`:
   - `orig\vsecomachina_0.6.1.zip`
   - The 8 `orig\FloralZones*.zip` files (or only the packs you want; the patch is safe with any subset)
   - `EcoMachinaFloralZonesCompat_v1.0.0.zip`
3. Don't unzip anything. Make sure there are no older copies of these mods in Mods.
4. Start the game and check the mod list shows "Eco Machina x Floral Zones Compat 1.0.0" as enabled.
5. Multiplayer: the server and every client need the patch, as they already need Eco Machina.
6. Existing worlds: only newly generated chunks get the fixed Cape and small-spruce canopies (see above).

**Uninstall:** delete `EcoMachinaFloralZonesCompat_v1.0.0.zip`. No blocks or items are added, so the world stays loadable. Already-generated Cape `grown` leaves will then stop decaying, the same as unpatched Cape `grown` leaves.

## Verification done here

| Check | Result |
|---|---|
| Patch files are strict JSON (Python `json.loads`) | PASS (4/4 files incl. modinfo) |
| `zipfile.testzip()` and `unzip -t` | PASS, `None` / "No errors detected" |
| Patch ops applied to the real target assets (`tools/apply_check.py`) | PASS, 14/14 ops, only the intended keys change |
| New leaf codes exist in the target blocktypes (`leaves-grown-<wood>`, `leavesbranchy-grown-<wood>` for the 3 Cape woods and `piceaglauca`) | PASS |
| Eco Machina classifier simulation, 18 species / 29 treegens (`tools/verify_species.py --patched`) | PASS, 0 problems (5 before the patch) |
| C# build | n/a, no C# needed |
| Installed to Mods | **At build time: No.** Mods now has the compat zip dated 2026-10-20 18:44; UNCONFIRMED, Nick to confirm |
