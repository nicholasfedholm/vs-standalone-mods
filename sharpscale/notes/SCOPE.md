# SharpScale scope (2026-10-28)

Goal: when the in-game render scale (`floatSettings.ssaa` < 1.0) is used, upscale the world image smoothly with sharpening instead of the vanilla nearest-pixel stretch. Target: Nick's Optimum client + Sunbright, RTX 3060, 2560x1440.

Evidence: `notes/vanilla_upscale.md`, `notes/overlap.md`, `notes/optimum_fsr.md` (explore-audit, static analysis only).

## Why the image is blocky today
- `ClientPlatformWindows.SetupDefaultFrameBuffers` (CPW:1080) sizes the Primary FBO to window x ssaa and sets its color texture to NEAREST when ssaa <= 1 (CPW:1126-1127, 1131-1132; LINEAR only for ssaa > 1).
- `BlitPrimaryToDefault` (CPW:1924-1937) is the upscale. It draws a fullscreen triangle with `ShaderPrograms.Blit` (`blit.fsh`: `texture(scene, texCoord)`) into the default framebuffer at full window size. The sample uses the texture's NEAREST filter. There is no `GL.BlitFramebuffer`.
- Order per frame (ScreenManager.cs:706-746): world, then postprocess (bloom, godrays, SSAO), then Luma/FXAA, then Final (all at low res), then the Blit upscale, then GUI at full res. GUI stays sharp.

## Optimum already has FSR1, but it is blocked here
- Optimum injects FSR1 EASU+RCAS into the same `BlitPrimaryToDefault` (donor CPW:2631-2685, FBO 18 RGBA8 at full res), gated by its own `RenderScale` (optimum.json, clamp 0.5-1.0, in-game Optimum tab values 1.0/0.85/0.77/0.67).
- With Sunbright loaded, Optimum's `.optimum/shader-compatibility.json` disables `RenderScale` ("external final shader owns the post-process contract"), so FSR cannot engage and the dropdown does nothing. RCAS sharpness is hard-coded (`fsr-rcas.fsh:27`).
- Possible Optimum cold-start bug (unverified): FBOs are built (donor :945) before the config loads (:639), so FBO 18 may not exist until the next rebuild.
- So with Sunbright kept, Nick has no smooth upscale today. That is the gap SharpScale fills.

## Hook (small)
- Harmony prefix on `Vintagestory.Client.NoObf.ClientPlatformWindows.BlitPrimaryToDefault()` (public, once per frame; same name on Optimum, its IL hooks are not renames).
- When `ClientSettings.SSAA < 1`, the offscreen buffer is on, and Optimum FSR is not active: bind the Default FB, set the full-window viewport, use our shader program (`sharpscale`, asset domain `sharpscale`), and bind `frameBuffers[0].ColorTextureIds[0]` on unit 0 with our own LINEAR sampler object. The texture's own state is not changed. Draw 3 vertices, then skip the original. Otherwise the vanilla or Optimum path runs untouched.
- Optimum guard: if `ClientSettings.OptimumRenderScale` exists, is < 1, and `frameBuffers[18]` is non-null, defer to Optimum (no double upscale).
- Any exception: log once, disable, fall back to vanilla.

## Shader plan
- v0.1 (prototype): bilinear taps plus AMD CAS-style adaptive sharpening (5 taps, `src/assets/sharpscale/shaders/sharpscale.fsh`). Mode 0 is bilinear only. Sharpness 0-1 is set in config and with the `.sharpscale` command for live A/B.
- v0.2 (if v0.1 looks soft): FSR1 EASU (12 taps, edge-adaptive) into a full-res RGBA8 FBO, then RCAS with configurable sharpness. AMD reference is MIT. Use our own asset names (`sharpscale-easu/rcas`), not Optimum's `fsr-*`.

## Compatibility
- Sunbright: overrides only `final.*` and `godrays.*`. Its `ShaderProgramBase.Use` postfix acts only on PassName final or godrays (ShaderBridge.cs:316-318). No blit changes. Safe. Units 11-14 avoided.
- Optimum: method names match. The guard prevents stacking with its FSR. Runtime patch order versus Optimum's IL hook on the same method is unverified. If Optimum's injected code runs before our prefix, SharpScale would never draw; one test run settles this.
- Screenshots: mega screenshot sets SSAA > 1, so SharpScale does not run.
- Vanilla `ssaa` watcher rebuilds FBOs live. The prefix reads `frameBuffers[0]` every frame, so nothing is cached.

## Cost and effort
- GPU: 5 bilinear taps per output pixel at 3.7 MP is about 0.05-0.15 ms on a 3060. This replaces the 1-tap blit, so the net cost is under 0.15 ms, well inside the 0.5 ms budget. EASU+RCAS v0.2: about 0.3-0.5 ms.
- Expected result: ssaa 0.75 keeps about 96 fps (vs 74 at 1.0) with an image close to native instead of blocky.
- Effort: v0.1 prototype ~1-2 h (built in this session). One in-game check of about 15 min (needs Nick's go). v0.2 EASU: +3-4 h.

## Test plan (needs Nick's go, one launch)
1. Install the zip (or use `--addModPath`), set ssaa 0.75, and launch Optimum on the peace world.
2. Check client-main.log for `[SharpScale] active` and no `[SharpScale]` errors.
3. In game, toggle `.sharpscale off` / `on` / `mode 0` and look at foliage and text-like edges. Take screenshots with F12 at each step.
4. Bench with vsbench: ssaa 0.75, SharpScale on vs off (ABBA). Expect a difference under 1 fps.
