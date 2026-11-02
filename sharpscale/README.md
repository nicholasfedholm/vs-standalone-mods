# SharpScale 0.2.0 (client; 0.2.0 installed 2026-10-29, replaced 0.1.0)

When the in-game render scale (ClientSettings.SSAA) is below 1, vanilla stretches the scene to the window with NEAREST filtering. SharpScale replaces that single draw (ClientPlatformWindows.BlitPrimaryToDefault, Harmony prefix) with a bilinear upscale plus AMD-CAS-style sharpening (assets/sharpscale/shaders). At SSAA >= 1 it does nothing and vanilla runs.

## Config
ModConfig/sharpscale.json (created on first run): `{ "Enabled": true, "Mode": 2, "Sharpness": 0.5, "RcasStops": 0.2 }` (fresh default Mode 2; existing files keep their Mode)
- Mode 0 = bilinear only, 1 = bilinear + CAS, 2 = FSR1 (EASU into a mod-owned full-res RGBA8 FBO, then RCAS to the default framebuffer). Sharpness 0..1 (Mode 1). RcasStops 0..2 (Mode 2, 0 = sharpest).

## Command (client chat)
`.sharpscale` prints state. `.sharpscale on|off`, `.sharpscale mode <0|1|2>`, `.sharpscale sharp <0..1>`, `.sharpscale rcas <0..2>` (saved to config, takes effect next frame). Use for in-game A/B.

## Guards
- Falls back to vanilla blit if the shader fails to compile, OffscreenBuffer is false, or any exception occurs (logged once, mod self-disables).
- Optimum client: if ClientSettings.OptimumRenderScale exists, is < 1, and frameBuffers[18] is set, SharpScale defers so Optimum's own FSR runs. Vanilla has no such member (handled via reflection).
- Uses texture unit 0, shader pass name "sharpscale" (Sunbright only touches "final"/"godrays").

## Test (0.2.0 is installed in Mods)
No copy needed. To test another build, run the game with `--addModPath` pointing at a folder with the unzipped mod (sharpscale\modpath_02 holds only the 0.2.0 zip, unzip it first); set render scale < 100% in graphics settings. Log lines start with `[SharpScale]` ("active: ssaa=... src=WxH ...").

## Build
`dotnet build -c Release` in this folder (net10.0, refs from %APPDATA%\Vintagestory). Package: modinfo.json, SharpScale.dll/.pdb, assets\sharpscale\shaders\* -> out\SharpScale-0.2.0.zip.


## 0.2.0 notes
FSR1 shaders (sharpscale_easu.fsh, sharpscale_rcas.fsh) are GLSL ports of AMD FidelityFX FSR 1.0 (MIT, notice in headers). If either shader fails to compile, the FBO is incomplete, or a GL exception occurs, one warning is logged and the session falls back to Mode 1. Log line on first blit (and on mode/size change): `[SharpScale] mode=2 FSR1 1920x1080 -> 2560x1440 ssaa=0.75 rcasStops=0.2`.


## Status

Nick's own mod. Not on ModDB yet (verified 2026-11-02). See notes/SCOPE.md and notes/BUILD_02.md for scope and build notes.
