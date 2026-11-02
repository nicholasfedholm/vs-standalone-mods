# earthtpbridge 0.1.0: in-game test plan for Nick

Zip: `earth-suite\out\earthtpbridge_0.1.0.zip` (SHA256 64dc61d4b8d21f44bd778241a4fe90bd386294f189dcf0266ac4239b5300442e). Needs Andris Earth 1.0.1 (plus its data mods) and Terra Prety. Server side only. Worldgen changes only affect newly generated chunks, so every test uses a NEW world.

## 0. Install (only after you approve)
1. Copy the zip into `VintagestoryData\Mods`. Earth, its data mods and Terra Prety stay as they are.
2. Start the game once and quit. This writes `VintagestoryData\ModConfig\earthtpbridge.json` with the defaults.

## 1. Log check (first, it takes one minute)
Create a new Earth world (play style Earth, the usual 512 height), let it load, then search `server-main.log` for `earthtpbridge`. You want to see:
- `Stood Terra Prety down (early, before Earth's transpilers): removed N Harmony patches` with N above 0.
- `Earth AridFill transpiler applied: True`. If it says False, Earth's dry-climate fill is still lost. Tell me.
- `Active in Earth world: <count> TP landforms, sea <Y>, map height 512, Earth DetailScale 1 -> 0.6`.
Bad signs: `late fallback` (detection missed, so AridFill may be lost), `Earth internals not found`, `Init failed`, or `No Terra Prety landforms found`.

## 2. A/B worlds (same seed)
- World A: bridge on (default config).
- World B: same seed, `"Enabled": false` in `earthtpbridge.json`. This is plain Andris Earth with Terra Prety still installed, which is your current setup.
- Optional World C: same seed with the bridge zip removed. This should match B. If it does not, tell me.
Use the same spawn and the same teleport coordinates in each world (`/tp x y z`), and take screenshots from the same spot.

## 3. Places to compare
- Lowland farm plains near the coast: A should show gentle Terra Prety rolling ground. B is smoother.
- Hills and foothills (a few hundred metres of real relief): this is where the bridge should be most visible.
- High mountains: little change on purpose. Earth's log height scale compresses detail at altitude. A should not look noisier than B.
- A big data river (for example the one nearest spawn on the map): see section 4.
- A sea coast with beaches, and a lake shore.

## 4. What to look for at rivers and coasts (the main risk)
- River channels and banks should be identical in A and B, block for block, within about 4 blocks of the water. Detail should fade in over about 16 blocks.
- No damming: water should never be cut off by a new ridge, and you should see no floating or dry river blocks, no waterfalls that are not in B, and no water spilling onto land.
- Coasts and beaches: land within a few blocks of sea level stays flat. No new cliffs at the waterline. No land pushed into the sea and no holes below sea level.
- Lake shores: these are the weak spot (lake fields were not used for masking). Look for odd lips or gaps around lakes.
- Villages and story structures: their pads should still be flat (reservations apply after the bridge).

## 5. Tuning knobs (`earthtpbridge.json`, new world after each change)
- `Strength` (1.0): more or less Terra Prety detail. Try 0.5 if A looks too busy, or 1.5 if you barely see it.
- `EarthDetailScale` (0.6): Earth's own detail. Set it to 1.0 to keep Earth's ridges as they are.
- `SlopeExponent` (1.0) and `SlopeFloor` (0.0): set `SlopeFloor` to 0.2 if mountains look too plain.
- `RiverFadeBlocks` (16) and `CoastFadeBlocks` (6): raise them if you see river or coast artefacts.
- `StandDownTerraPrety` (true): leave it on.

## 6. Performance
Compare chunk generation speed in A and B (fly in one direction for 2 minutes and look for loading holes). The bridge adds a lattice probe of about one extra Earth column per 16 columns, plus noise.

## 7. Report back
For A vs B: log lines from section 1, screenshots of the places in section 3, and yes or no for each item in section 4.
