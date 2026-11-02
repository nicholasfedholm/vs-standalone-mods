# earthtpbridge design (Andris Earth 1.0.1 x Terra Prety 7.11.2-pre.1, VS 1.22.7)

Evidence files: `work/FEASIBILITY.md` (Phase 1), `work/P2_E1E2_findings.md` (Phase 2 step 1 auditors E1, E2, E3, T). Line numbers are of the decompiled output in `work/dec`.

## 1. Hook choice

Harmony postfix on `EarthMap.Core.TerrainModel.GetColumnWithoutReservations(double x, double z)` (public, TerrainModel.cs:449).

- Every column of `EarthWorldGen.GenerateTerrain` comes from `TerrainModel.GetColumn` (EarthWorldGen.cs:1402, margin ring :1423); no batch or grid path exists.
- `GetColumn` (:429) calls only `GetColumnWithoutReservations` (:431), then adds a reservation offset to `Top` (:443, `Top += round(num2*num)`, toward `TerrainReservation.targetTop`). Patching the inner method means story and village reservations still flatten their sites on top of the bridge's detail.
- The returned `Column` is a struct with no cache (E1 Q4), so every caller (trees, geology, ores, spawn search, structure guards, map colours, river audit) sees the same adjusted `Top`. Base terrain, strata and later passes stay consistent.
- `Top` is the surface Y GenerateTerrain fills to (:1492-1496) and writes to the heightmap (:1520). The postfix changes only `Top` (and `WaterTop` when it equals the old `Top`, which is a dry column).
- Rejected: postfix on `GetColumn` (would fight reservations); a Terrain-pass handler after Earth (redoes block work, and later Earth passes would not see the change); patching private `Detail` (not needed, see 4).
- Only the model that `EarthWorldGen.Instance.Model` returns is touched (`__instance` check), and only when `EarthWorldGen.Active` is true.

## 2. Terra Prety stand-down

Same mechanism as mcleanlt (`OtherWorldgenMods.cs:99-108, 389-402`): for each `Harmony.GetAllPatchedMethods()`, unpatch every prefix, postfix, transpiler and finalizer whose `PatchMethod.DeclaringType.Assembly` is TP's assembly (found from the `terraprety` mod's systems). TP's ModSystems keep running; their `GenTerraPrety`/`GenRivers` generators are already dead (`ShouldLoad` false).

Timing matters, found in step 1: TP's `GenBlockLayers.OnChunkColumnGeneration` transpiler (TP Patch.cs:103-125, applied in StartPre) rewrites the `40f` constant to `0f`; Earth's AridFill transpiler (EarthWorldGen.cs:703-718, applied in Earth StartServerSide, ExecuteOrder 0.7) searches for that `40f` and silently fails when TP got there first. So the bridge stands TP down in its own `StartServerSide` at ExecuteOrder 0.69, before Earth applies its transpiler. Earth world detection at that point: `earth` mod enabled, `SaveGame.WorldType == "standard"`, `SaveGame.PlayStyle` equals `earth` (Earth's own guard, EarthWorldOptions.cs:81-83). A late fallback in InitWorldGen re-checks `EarthWorldGen.Active` and unpatches then if the early check missed (AridFill stays lost in that case; logged).

## 3. Landform mapping (Earth column to TP landform)

Reference: mcleanlt `TerraPretyLandforms.Pick` (:230) and `EarthLandformLayer` (:72-101).

- Pick cells of 64x64 blocks. For each cell, sample `Elev` (metres) on a 5x5 grid at 16-block spacing centred on the cell; roughness `r = 3 * stddev(Elev of land samples)` (mcleanlt's definition).
- `h = Ladder(r)`: piecewise linear {0, 60, 200, 500, 1200, 3000} m to {0, 0.15, 0.25, 0.45, 0.65, 1.0}; if mean land Elev > 30 m, `h = max(h, 0.075)`.
- Eligible TP rows: `MinHeight <= h <= MaxHeight` from `terraprety:worldgen/landformheights.json`, read directly from the asset store; weights and octaves from the patched `game:worldgen/landforms.json` (TP replaces its `/variants`; read after patching). Rows without a landform or with weight 0 are skipped. Weighted pick with a hash of (cell x, cell z, seed). No eligible row: fall back to the eligible row nearest in band centre.
- Per landform: octave amplitudes `terrainOctaves[0..8]` with octaves 0-2 zeroed (large shapes are Earth's job, mcleanlt Resize does the same); band `BandFor((Min+Max)/2) * (mapSizeY/256) * 1.5` with BandFor piecewise linear over {4, 9, 16, 26, 40} at {0.075, 0.2, 0.35, 0.55, 0.825} (mcleanlt :176, :320).
- Detail shape `N(x,z) = sum_k a_k * simplex(x * f0 * 2^k, z * f0 * 2^k) / sum_k a_k`, `f0 = 0.000306186 / max(1, mapSizeY/256)` (mcleanlt :157), own seeded 2D simplex. Range about [-1, 1], zero mean.
- Seams: the four nearest pick-cell centres are blended bilinearly, so landform changes never step.

## 4. Amplitude

`dy = Strength * 0.5 * band * N * SlopeFactor(Elev) * Mask`, rounded, clamped to `+-MaxOffsetBlocks`.

- `SlopeFactor(h) = clamp((Slope(h) / Slope(0))^SlopeExponent, SlopeFloor, 1)` using Earth's own `VerticalScale.Slope` (VerticalScale.cs:114). For the default log curve this is `LandH0 / (LandH0 + h)`, from `d/dh [s*ln(1+h/LandH0)] = s/(LandH0+h)`. TP's band is treated as defined at sea level, then compressed exactly as Earth compresses real relief. `h` is clamped at 0. With `LinearLand` the factor is 1.
- Relative to Earth's sea level (`TerrainModel.SeaLevel`, :196): a column above sea is never pushed to or below `SeaLevel + 1`; the coast mask below starts at sea level.
- Double detail: Earth's own ridged `Detail` term is scaled by the public `TerrainModel.DetailScale` (:96, used :720). The bridge multiplies it by `EarthDetailScale` (default 0.6) once at world init, so the two detail sources do not stack into noise. No patch on the private method.

## 5. River and coast mask

`Mask = MaskLattice(x,z) * CoastMask(Top)`, and 0 for any blocked column.

- Blocked column: `Water != 0`, `River`, `NearRiver`, `DryRiver`, `Gutter`, `Beach`, `Rapid`, `RapidsReach`, `Fall > 0`, `Ramp > 0`, `Spill > 0`, `Edge > 0`, or ice (`IceBottom != int.MaxValue`, TerrainModel.cs:521).
- Lattice: every 4 blocks, the blocked flag of the raw Earth column (probe calls run with a thread-static guard so the postfix does not recurse). A lattice point's mask is `smoothstep((d - 4) / RiverFadeBlocks)` where `d` is the distance to the nearest blocked lattice point within `RiverFadeBlocks + 4`. Columns blend the 4 surrounding lattice masks bilinearly. Rivers and coasts therefore keep Earth's exact heights, and detail ramps in over `RiverFadeBlocks` (default 16).
- `CoastMask = smoothstep((Top - SeaLevel - 1) / CoastFadeBlocks)` (default 6): low coastal land stays flat even where the lattice misses a thin feature.
- River bed depth relative versus absolute (TerrainModel.cs:1127-1175) is UNVERIFIED (the auditor's read was hook-blocked). The mask makes this moot: the bridge never changes a river, near-river or water column.
- Caches: `ConcurrentDictionary` keyed by lattice and pick cell; values are pure functions of position, so the caches are cleared when large (no effect on output).

## 6. Config (`ModConfig/earthtpbridge.json`, server side)

| Key | Default | Meaning |
|---|---|---|
| Enabled | true | Master switch: false = no stand-down, no detail (A/B test) |
| StandDownTerraPrety | true | Unpatch TP in Earth worlds |
| Strength | 1.0 | Multiplier on TP detail amplitude |
| EarthDetailScale | 0.6 | Multiplier on Earth's own DetailScale (1.0 = untouched) |
| SlopeExponent | 1.0 | Exponent on the log-curve slope ratio |
| SlopeFloor | 0.0 | Minimum slope factor |
| RiverFadeBlocks | 16 | Distance over which detail fades in from rivers, lakes, sea, beaches |
| CoastFadeBlocks | 6 | Height above sea over which detail fades in |
| MaxOffsetBlocks | 24 | Hard cap on the added offset |

Worldgen changes affect only newly generated chunks. Changing any value in an existing world creates seams at the old/new chunk border.

## 7. Known limits

- Depends on Earth internals (`GetColumnWithoutReservations`, `Column` field names, internal `Instance`). An Earth update can break it; the mod logs and disables itself if the method or field lookups fail.
- Lake fields `NearLakeTop`, `LakeRingTop`, `LakeHoldTop` are not used for masking (their no-lake values were not audited); lake shores rely on `Water`, `Edge`, `Spill` and the lattice.
- In multiplayer, a client-side Earth map renderer using its own `TerrainModel` would not see the detail (only the server model is patched).
