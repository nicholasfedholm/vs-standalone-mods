using HarmonyLib;
using OpenTK.Graphics.OpenGL4;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.MathTools;
using Vintagestory.Client.NoObf;

namespace SharpScale;

public class SharpScaleMod : ModSystem
{
    public const string HarmonyId = "sharpscale";

    private static SharpScaleMod? inst;
    private ICoreClientAPI capi = null!;
    private Harmony? harmony;
    private SharpScaleConfig cfg = new();
    private IShaderProgram? prog;
    private bool programOk;
    private bool disabled;
    private int sampler;
    private int vao;
    private bool loggedOptimum;
    private string? lastActiveLog;

    // FSR1 (Mode 2) state
    private IShaderProgram? easuProg, rcasProg;
    private bool easuOk, rcasOk;
    private bool fsrFailed;          // set once; session falls back to Mode 1
    private int fsrFbo, fsrTex, fsrW, fsrH;

    // reflection caches (resolved once)
    private static System.Reflection.FieldInfo? fiFrameBuffers;
    private static System.Reflection.FieldInfo? fiOffscreen;
    private static System.Reflection.PropertyInfo? piOffscreen;
    private static System.Reflection.PropertyInfo? piOptimumScale;
    private static System.Reflection.FieldInfo? fiOptimumScale;
    private static System.Reflection.FieldInfo? fiWindow;
    private static System.Reflection.PropertyInfo? piClientSize;
    private static bool reflectionResolved;

    public override bool ShouldLoad(EnumAppSide forSide) => forSide == EnumAppSide.Client;

    public override void StartClientSide(ICoreClientAPI api)
    {
        capi = api;
        inst = this;
        try { cfg = api.LoadModConfig<SharpScaleConfig>(SharpScaleConfig.FileName) ?? new SharpScaleConfig(); }
        catch (Exception ex) { api.Logger.Warning("[SharpScale] config load failed: {0}", ex.Message); cfg = new SharpScaleConfig(); }
        cfg.Mode = Math.Clamp(cfg.Mode, 0, 2);
        cfg.Sharpness = GameMath.Clamp(cfg.Sharpness, 0f, 1f);
        cfg.RcasStops = GameMath.Clamp(cfg.RcasStops, 0f, 2f);
        SaveConfig();
        api.Logger.Notification("[SharpScale] {0} loaded: enabled={1} mode={2} sharpness={3} rcasStops={4}", Mod.Info.Version, cfg.Enabled, cfg.Mode, cfg.Sharpness, cfg.RcasStops);

        ResolveReflection();
        RegisterShader();
        api.Event.ReloadShader += OnReloadShader;

        harmony = new Harmony(HarmonyId);
        var target = AccessTools.Method(typeof(ClientPlatformWindows), nameof(ClientPlatformWindows.BlitPrimaryToDefault));
        var prefix = AccessTools.Method(typeof(SharpScaleMod), nameof(Prefix));
        if (target == null || prefix == null)
        {
            api.Logger.Error("[SharpScale] could not resolve BlitPrimaryToDefault; mod inactive.");
            disabled = true;
        }
        else
        {
            harmony.Patch(target, prefix: new HarmonyMethod(prefix));
        }

        RegisterCommand(api);
    }

    private static void ResolveReflection()
    {
        if (reflectionResolved) return;
        reflectionResolved = true;
        var t = typeof(ClientPlatformWindows);
        fiFrameBuffers = AccessTools.Field(t, "frameBuffers");
        fiOffscreen = AccessTools.Field(t, "OffscreenBuffer");
        if (fiOffscreen == null) piOffscreen = AccessTools.Property(t, "OffscreenBuffer");
        piOptimumScale = AccessTools.Property(typeof(ClientSettings), "OptimumRenderScale");
        if (piOptimumScale == null) fiOptimumScale = AccessTools.Field(typeof(ClientSettings), "OptimumRenderScale");
        fiWindow = AccessTools.Field(t, "window");
        piClientSize = fiWindow == null ? null : AccessTools.Property(fiWindow.FieldType, "ClientSize");
    }

    private void RegisterShader()
    {
        try
        {
            var p = capi.Shader.NewShaderProgram();
            p.AssetDomain = Mod.Info.ModID;
            capi.Shader.RegisterFileShaderProgram("sharpscale", p);
            programOk = p.Compile();
            prog = p;
            if (!programOk) capi.Logger.Error("[SharpScale] shader failed to compile; falling back to vanilla blit.");
        }
        catch (Exception ex)
        {
            programOk = false;
            capi.Logger.Error("[SharpScale] shader registration failed: {0}", ex);
        }

        easuProg = RegisterFsrShader("sharpscale_easu", out easuOk);
        rcasProg = RegisterFsrShader("sharpscale_rcas", out rcasOk);
        if (easuOk && rcasOk) fsrFailed = false; // a shader reload may repair an earlier failure
    }

    private IShaderProgram? RegisterFsrShader(string name, out bool ok)
    {
        try
        {
            var p = capi.Shader.NewShaderProgram();
            p.AssetDomain = Mod.Info.ModID;
            capi.Shader.RegisterFileShaderProgram(name, p);
            ok = p.Compile();
            return p;
        }
        catch (Exception ex)
        {
            ok = false;
            capi.Logger.Debug("[SharpScale] {0} registration exception: {1}", name, ex.Message);
            return null;
        }
    }

    private bool OnReloadShader()
    {
        RegisterShader();
        return programOk;
    }

    private void SaveConfig()
    {
        try { capi.StoreModConfig(cfg, SharpScaleConfig.FileName); }
        catch (Exception ex) { capi.Logger.Warning("[SharpScale] config save failed: {0}", ex.Message); }
    }

    private void RegisterCommand(ICoreClientAPI api)
    {
        string State() => string.Format("SharpScale {0}: enabled={1} mode={2}{3} sharpness={4:0.00} rcasStops={5:0.00} ssaa={6:0.00} shader={7} fsr={8} disabledByError={9}",
            Mod.Info.Version, cfg.Enabled, cfg.Mode, (cfg.Mode == 2 && fsrFailed) ? "(fallback->1)" : "", cfg.Sharpness, cfg.RcasStops, ClientSettings.SSAA,
            programOk ? "ok" : "failed", (easuOk && rcasOk) ? (fsrFailed ? "failed" : "ok") : "shader-failed", disabled);

        var parsers = api.ChatCommands.Parsers;
        api.ChatCommands.Create("sharpscale")
            .WithDescription("SharpScale upscale sharpening (active only when render scale < 1)")
            .HandleWith(_ => TextCommandResult.Success(State()))
            .BeginSubCommand("on").WithDescription("Enable")
                .HandleWith(_ => { cfg.Enabled = true; SaveConfig(); return TextCommandResult.Success(State()); })
            .EndSubCommand()
            .BeginSubCommand("off").WithDescription("Disable (vanilla nearest upscale)")
                .HandleWith(_ => { cfg.Enabled = false; SaveConfig(); return TextCommandResult.Success(State()); })
            .EndSubCommand()
            .BeginSubCommand("mode").WithDescription("0 = bilinear, 1 = bilinear + CAS, 2 = FSR1 (EASU + RCAS)")
                .WithArgs(parsers.IntRange("mode", 0, 2))
                .HandleWith(a => { cfg.Mode = (int)a[0]; SaveConfig(); return TextCommandResult.Success(State()); })
            .EndSubCommand()
            .BeginSubCommand("sharp").WithDescription("Sharpness 0..1 (Mode 1 CAS)")
                .WithArgs(parsers.Float("value"))
                .HandleWith(a => { cfg.Sharpness = GameMath.Clamp((float)a[0], 0f, 1f); SaveConfig(); return TextCommandResult.Success(State()); })
            .EndSubCommand()
            .BeginSubCommand("rcas").WithDescription("RCAS attenuation in stops 0..2 (Mode 2), 0 = sharpest")
                .WithArgs(parsers.Float("stops"))
                .HandleWith(a => { cfg.RcasStops = GameMath.Clamp((float)a[0], 0f, 2f); SaveConfig(); return TextCommandResult.Success(State()); })
            .EndSubCommand();
    }

    // Harmony prefix: return true = run vanilla, false = skip it.
    public static bool Prefix(ClientPlatformWindows __instance)
    {
        var self = inst;
        if (self == null) return true;
        try { return self.RunBlit(__instance); }
        catch (Exception ex)
        {
            self.disabled = true;
            self.capi.Logger.Error("[SharpScale] blit failed, disabling and falling back to vanilla: {0}", ex);
            try { GL.BindVertexArray(0); GL.BindSampler(0, 0); } catch { }
            return true;
        }
    }

    private bool RunBlit(ClientPlatformWindows plat)
    {
        if (disabled || !cfg.Enabled || !programOk || prog == null) return true;
        float ssaa = ClientSettings.SSAA;
        if (!(ssaa < 0.999f)) return true;

        if (fiOffscreen != null && !(bool)fiOffscreen.GetValue(plat)!) return true;
        if (fiOffscreen == null && piOffscreen != null && !(bool)piOffscreen.GetValue(plat)!) return true;

        var fbs = fiFrameBuffers?.GetValue(plat) as List<FrameBufferRef>;
        if (fbs == null || fbs.Count == 0 || fbs[0] == null) return true;

        // Optimum client runs its own FSR in this method when OptimumRenderScale < 1.
        if (OptimumFsrActive(fbs))
        {
            if (!loggedOptimum) { loggedOptimum = true; capi.Logger.Notification("[SharpScale] deferring to Optimum FSR (OptimumRenderScale < 1)."); }
            return true;
        }

        FrameBufferRef fb0 = fbs[0];
        if (fb0.ColorTextureIds == null || fb0.ColorTextureIds.Length == 0 || fb0.Width <= 0 || fb0.Height <= 0) return true;

        EnsureSamplerAndVao();

        GetWindowSize(plat, out int w, out int h);

        int mode = Math.Clamp(cfg.Mode, 0, 2);
        if (mode == 2 && !fsrFailed)
        {
            if (TryRunFsr(plat, fb0, w, h))
            {
                LogActive(ssaa, fb0, w, h, 2);
                return false;
            }
            // TryRunFsr logged the warning and set fsrFailed; continue with Mode 1 this frame.
        }
        int effMode = mode == 2 ? 1 : mode;

        plat.LoadFrameBuffer(EnumFrameBuffer.Default);
        GL.Viewport(0, 0, w, h);

        prog.Use();
        prog.BindTexture2D("scene", fb0.ColorTextureIds[0], 0);
        GL.BindSampler(0, sampler);
        prog.Uniform("srcTexel", new Vec2f(1f / fb0.Width, 1f / fb0.Height));
        prog.Uniform("sharpness", cfg.Sharpness);
        prog.Uniform("mode", effMode);
        GL.BindVertexArray(vao);
        GL.DrawArrays(PrimitiveType.Triangles, 0, 3);
        GL.BindVertexArray(0);
        GL.BindSampler(0, 0);
        prog.Stop();

        LogActive(ssaa, fb0, w, h, effMode);
        return false;
    }

    private void EnsureSamplerAndVao()
    {
        if (sampler == 0)
        {
            sampler = GL.GenSampler();
            GL.SamplerParameter(sampler, SamplerParameterName.TextureMinFilter, (int)TextureMinFilter.Linear);
            GL.SamplerParameter(sampler, SamplerParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
            GL.SamplerParameter(sampler, SamplerParameterName.TextureWrapS, (int)TextureWrapMode.ClampToEdge);
            GL.SamplerParameter(sampler, SamplerParameterName.TextureWrapT, (int)TextureWrapMode.ClampToEdge);
        }
        if (vao == 0) vao = GL.GenVertexArray();
    }

    // Logs once per distinct (mode, sizes) state so the bench log proves which arm ran.
    private void LogActive(float ssaa, FrameBufferRef fb0, int w, int h, int effMode)
    {
        bool fellBack = cfg.Mode == 2 && effMode != 2;
        string key = effMode + ":" + fb0.Width + "x" + fb0.Height + ":" + w + "x" + h + ":" + fellBack;
        if (key == lastActiveLog) return;
        lastActiveLog = key;
        string name = effMode == 2 ? "FSR1" : effMode == 1 ? "bilinear+CAS" : "bilinear";
        string extra = effMode == 2 ? string.Format("rcasStops={0}", cfg.RcasStops) : effMode == 1 ? string.Format("sharpness={0}", cfg.Sharpness) : "";
        capi.Logger.Notification("[SharpScale] mode={0} {1} {2}x{3} -> {4}x{5} ssaa={6} {7}{8}",
            effMode, name, fb0.Width, fb0.Height, w, h, ssaa, extra, fellBack ? " (requested mode 2, fell back)" : "");
    }

    private void FsrFail(string reason)
    {
        if (fsrFailed) return;
        fsrFailed = true;
        capi.Logger.Warning("[SharpScale] FSR1 unavailable ({0}); falling back to Mode 1 for this session.", reason);
    }

    // Creates or resizes the mod-owned full-res RGBA8 intermediate. Returns false on failure.
    private bool EnsureFsrFbo(int w, int h)
    {
        if (fsrFbo != 0 && fsrTex != 0 && fsrW == w && fsrH == h) return true;
        DeleteFsrFbo();
        int prevTex = GL.GetInteger(GetPName.TextureBinding2D);
        int prevFbo = GL.GetInteger(GetPName.FramebufferBinding);
        int tex = GL.GenTexture();
        GL.BindTexture(TextureTarget.Texture2D, tex);
        GL.TexImage2D(TextureTarget.Texture2D, 0, PixelInternalFormat.Rgba8, w, h, 0, PixelFormat.Rgba, PixelType.UnsignedByte, IntPtr.Zero);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMinFilter, (int)TextureMinFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureMagFilter, (int)TextureMagFilter.Linear);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapS, (int)TextureWrapMode.ClampToEdge);
        GL.TexParameter(TextureTarget.Texture2D, TextureParameterName.TextureWrapT, (int)TextureWrapMode.ClampToEdge);
        GL.BindTexture(TextureTarget.Texture2D, prevTex);

        int fbo = GL.GenFramebuffer();
        GL.BindFramebuffer(FramebufferTarget.Framebuffer, fbo);
        GL.FramebufferTexture2D(FramebufferTarget.Framebuffer, FramebufferAttachment.ColorAttachment0, TextureTarget.Texture2D, tex, 0);
        var status = GL.CheckFramebufferStatus(FramebufferTarget.Framebuffer);
        GL.BindFramebuffer(FramebufferTarget.Framebuffer, prevFbo);
        if (status != FramebufferErrorCode.FramebufferComplete)
        {
            GL.DeleteFramebuffer(fbo);
            GL.DeleteTexture(tex);
            FsrFail("intermediate framebuffer incomplete: " + status);
            return false;
        }
        fsrFbo = fbo; fsrTex = tex; fsrW = w; fsrH = h;
        return true;
    }

    private void DeleteFsrFbo()
    {
        try
        {
            if (fsrFbo != 0) GL.DeleteFramebuffer(fsrFbo);
            if (fsrTex != 0) GL.DeleteTexture(fsrTex);
        }
        catch { }
        fsrFbo = 0; fsrTex = 0; fsrW = 0; fsrH = 0;
    }

    // Pass A: EASU (render-res primary -> full-res RGBA8 FBO). Pass B: RCAS (FBO -> default framebuffer).
    private bool TryRunFsr(ClientPlatformWindows plat, FrameBufferRef fb0, int w, int h)
    {
        if (!easuOk || !rcasOk || easuProg == null || rcasProg == null) { FsrFail("EASU/RCAS shader failed to compile"); return false; }
        try
        {
            if (!EnsureFsrFbo(w, h)) return false;

            plat.LoadFrameBuffer(EnumFrameBuffer.Default); // keep the platform's tracked FB state sane
            GL.BindFramebuffer(FramebufferTarget.Framebuffer, fsrFbo);
            GL.Viewport(0, 0, w, h);
            GL.BindVertexArray(vao);
            GL.BindSampler(0, sampler);

            easuProg.Use();
            easuProg.BindTexture2D("scene", fb0.ColorTextureIds[0], 0);
            easuProg.Uniform("outSize", new Vec2f(w, h));
            GL.DrawArrays(PrimitiveType.Triangles, 0, 3);
            easuProg.Stop();

            plat.LoadFrameBuffer(EnumFrameBuffer.Default);
            GL.BindFramebuffer(FramebufferTarget.Framebuffer, 0); // in case the platform skipped the bind
            GL.Viewport(0, 0, w, h);

            rcasProg.Use();
            rcasProg.BindTexture2D("scene", fsrTex, 0);
            rcasProg.Uniform("rcasCon", (float)Math.Pow(2.0, -cfg.RcasStops));
            GL.DrawArrays(PrimitiveType.Triangles, 0, 3);
            rcasProg.Stop();

            GL.BindVertexArray(0);
            GL.BindSampler(0, 0);
            return true;
        }
        catch (Exception ex)
        {
            try
            {
                GL.BindVertexArray(0); GL.BindSampler(0, 0);
                GL.BindFramebuffer(FramebufferTarget.Framebuffer, 0);
            }
            catch { }
            FsrFail("exception: " + ex.Message);
            return false;
        }
    }

    private bool OptimumFsrActive(List<FrameBufferRef> fbs)
    {
        object? v = null;
        if (piOptimumScale != null) v = piOptimumScale.GetValue(null);
        else if (fiOptimumScale != null) v = fiOptimumScale.GetValue(null);
        if (v == null) return false;
        float scale = Convert.ToSingle(v);
        return scale < 1f && fbs.Count > 18 && fbs[18] != null;
    }

    private void GetWindowSize(ClientPlatformWindows plat, out int w, out int h)
    {
        w = capi.Render.FrameWidth; h = capi.Render.FrameHeight;
        try
        {
            if (fiWindow != null && piClientSize != null)
            {
                object? win = fiWindow.GetValue(plat);
                object? size = win == null ? null : piClientSize.GetValue(win);
                if (size is OpenTK.Mathematics.Vector2i v && v.X > 0 && v.Y > 0) { w = v.X; h = v.Y; return; }
            }
            var ws = plat.WindowSize;
            if (ws != null && ws.Width > 0 && ws.Height > 0) { w = ws.Width; h = ws.Height; }
        }
        catch { }
    }

    public override void Dispose()
    {
        try { harmony?.UnpatchAll(HarmonyId); } catch { }
        harmony = null;
        try
        {
            if (sampler != 0) { GL.DeleteSampler(sampler); sampler = 0; }
            if (vao != 0) { GL.DeleteVertexArray(vao); vao = 0; }
        }
        catch { }
        DeleteFsrFbo();
        if (inst == this) inst = null;
        base.Dispose();
    }
}
