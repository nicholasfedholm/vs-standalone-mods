using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using EarthMap;
using EarthMap.Core;
using EarthTpBridge.Core;
using HarmonyLib;
using Newtonsoft.Json.Linq;
using Vintagestory.API.Common;
using Vintagestory.API.Server;

namespace EarthTpBridge
{
    /// <summary>
    /// Andris Earth x Terra Prety bridge. In Earth worlds only: stands TP's Harmony patches down and adds TP
    /// landform detail to Earth's columns through a postfix on TerrainModel.GetColumnWithoutReservations.
    /// </summary>
    public class EarthTpBridgeModSystem : ModSystem
    {
        public const string HarmonyId = "earthtpbridge";

        internal static EarthTpBridgeModSystem? Active;
        internal static readonly FieldInfo? EarthInstanceField = AccessTools.Field(typeof(EarthWorldGen), "Instance");

        internal ICoreServerAPI sapi = null!;
        internal BridgeConfig Config = new();
        Harmony? harmony;
        bool tpStoodDown;

        readonly object initLock = new();
        internal TerrainModel? model;
        internal BridgeEngine? engine;
        internal volatile bool disabled;

        public override bool ShouldLoad(EnumAppSide forSide) => forSide == EnumAppSide.Server;

        // Before Earth's StartServerSide (0.7), so Earth's AridFill transpiler sees GenBlockLayers without TP's edit.
        public override double ExecuteOrder() => 0.69;

        public override void StartServerSide(ICoreServerAPI api)
        {
            sapi = api;
            try
            {
                Config = api.LoadModConfig<BridgeConfig>("earthtpbridge.json") ?? new BridgeConfig();
                api.StoreModConfig(Config, "earthtpbridge.json");
            }
            catch (Exception e)
            {
                Mod.Logger.Error("Bad earthtpbridge.json, using defaults: {0}", e.Message);
                Config = new BridgeConfig();
            }
            if (!Config.Enabled)
            {
                Mod.Logger.Notification("Disabled by config (Enabled=false): Terra Prety and Earth left untouched.");
                return;
            }

            harmony = new Harmony(HarmonyId);
            if (Config.StandDownTerraPrety && LooksLikeEarthWorld(api))
            {
                StandDownTerraPrety("early, before Earth's transpilers");
            }

            var target = AccessTools.Method(typeof(TerrainModel), "GetColumnWithoutReservations", new[] { typeof(double), typeof(double) });
            if (target == null || EarthInstanceField == null)
            {
                Mod.Logger.Error("Earth internals not found (GetColumnWithoutReservations or EarthWorldGen.Instance); detail disabled. Earth version changed?");
                return;
            }
            harmony.Patch(target, postfix: new HarmonyMethod(typeof(ColumnPatch), nameof(ColumnPatch.Postfix)));
            Active = this;
            api.Event.ServerRunPhase(EnumServerRunPhase.RunGame, LogAridFill);
        }

        static bool LooksLikeEarthWorld(ICoreServerAPI api)
        {
            var sg = api.WorldManager.SaveGame;
            return api.ModLoader.IsModEnabled("earth")
                && sg != null
                && string.Equals(sg.WorldType, "standard", StringComparison.OrdinalIgnoreCase)
                && string.Equals(sg.PlayStyle, "earth", StringComparison.OrdinalIgnoreCase);
        }

        internal void StandDownTerraPrety(string when)
        {
            if (tpStoodDown || harmony == null) return;
            tpStoodDown = true;
            var tp = sapi.ModLoader.GetMod("terraprety");
            var asm = tp?.Systems?.FirstOrDefault()?.GetType().Assembly;
            if (asm == null)
            {
                Mod.Logger.Notification("Terra Prety not loaded; nothing to stand down.");
                return;
            }
            int removed = 0;
            foreach (var original in Harmony.GetAllPatchedMethods().ToList())
            {
                var info = Harmony.GetPatchInfo(original);
                if (info == null) continue;
                var all = info.Prefixes.Concat(info.Postfixes).Concat(info.Transpilers).Concat(info.Finalizers).ToList();
                foreach (var p in all)
                {
                    if (p.PatchMethod?.DeclaringType?.Assembly != asm) continue;
                    harmony.Unpatch(original, p.PatchMethod);
                    removed++;
                }
            }
            Mod.Logger.Notification("Stood Terra Prety down ({0}): removed {1} Harmony patches from {2}.", when, removed, asm.GetName().Name);
        }

        void LogAridFill()
        {
            var f = AccessTools.Field(typeof(EarthWorldGen), "aridFillPatched");
            object? v = null;
            try { v = f?.GetValue(f.IsStatic ? null : EarthInstanceField?.GetValue(null)); } catch { }
            Mod.Logger.Notification("Earth AridFill transpiler applied: {0}", v ?? "unknown (field not found)");
        }

        /// <summary>Builds the engine the first time Earth's active model asks for a column. Returns null when not an Earth world.</summary>
        internal BridgeEngine? EngineFor(TerrainModel instance)
        {
            if (disabled) return null;
            if (ReferenceEquals(instance, model)) return engine;
            var earth = EarthInstanceField?.GetValue(null) as EarthWorldGen;
            if (earth == null || !earth.Active || !ReferenceEquals(earth.Model, instance)) return null;
            lock (initLock)
            {
                if (ReferenceEquals(instance, model)) return engine;
                try
                {
                    if (Config.StandDownTerraPrety) StandDownTerraPrety("late fallback; Earth AridFill may be lost");
                    var defs = LoadLandforms();
                    if (defs.Count == 0)
                    {
                        Mod.Logger.Warning("No Terra Prety landforms found; detail disabled.");
                        disabled = true;
                        return null;
                    }
                    double before = instance.DetailScale;
                    instance.DetailScale = before * Config.EarthDetailScale;
                    var vert = instance.Vertical;
                    int mapY = sapi.WorldManager.MapSizeY;
                    var built = new BridgeEngine(Config, defs, sapi.World.Seed, mapY, instance.SeaLevel,
                        h => vert.Slope(h), (x, z) => ColumnPatch.Probe(instance, x, z));
                    engine = built;
                    model = instance;
                    Mod.Logger.Notification("Active in Earth world: {0} TP landforms, sea {1}, map height {2}, Earth DetailScale {3} -> {4}, strength {5}.",
                        defs.Count, instance.SeaLevel, mapY, before, instance.DetailScale, Config.Strength);
                    return engine;
                }
                catch (Exception e)
                {
                    Mod.Logger.Error("Init failed, detail disabled: {0}", e);
                    disabled = true;
                    return null;
                }
            }
        }

        /// <summary>Joins TP's landformheights.json rows with weights and octaves from the (TP-patched) vanilla landforms asset.</summary>
        List<LandformDef> LoadLandforms()
        {
            var result = new List<LandformDef>();
            var heights = sapi.Assets.TryGet(new AssetLocation("terraprety", "worldgen/landformheights.json"));
            var landforms = sapi.Assets.TryGet(new AssetLocation("game", "worldgen/landforms.json"));
            if (heights == null || landforms == null) return result;
            var byCode = new Dictionary<string, JObject>(StringComparer.OrdinalIgnoreCase);
            foreach (var v in JObject.Parse(landforms.ToText())["variants"] as JArray ?? new JArray())
            {
                if (v is JObject o && o["code"]?.ToString() is string c) byCode[c] = o;
            }
            foreach (var row in JObject.Parse(heights.ToText())["variants"] as JArray ?? new JArray())
            {
                string? code = row["code"]?.ToString();
                if (code == null || !byCode.TryGetValue(code, out var lf)) continue;
                var oct = (lf["terrainOctaves"] as JArray)?.Select(t => (double)t).ToArray() ?? Array.Empty<double>();
                result.Add(new LandformDef
                {
                    Code = code,
                    MinHeight = (double?)row["minHeight"] ?? 0,
                    MaxHeight = (double?)row["maxHeight"] ?? 1,
                    Weight = (double?)lf["weight"] ?? 1,
                    Octaves = oct,
                });
            }
            return result;
        }

        public override void Dispose()
        {
            harmony?.UnpatchAll(HarmonyId);
            if (ReferenceEquals(Active, this)) Active = null;
        }
    }

    public static class ColumnPatch
    {
        [ThreadStatic] static bool probing;

        internal static bool IsBlocked(in TerrainModel.Column c) =>
            c.Water != 0 || c.River || c.NearRiver || c.DryRiver || c.Gutter || c.Beach || c.Rapid || c.RapidsReach
            || c.Fall > 0 || c.Ramp > 0 || c.Spill > 0 || c.Edge > 0 || c.IceBottom != int.MaxValue;

        /// <summary>Raw Earth column; the guard keeps the postfix from applying to its own probes.</summary>
        internal static ColumnInfo Probe(TerrainModel model, int x, int z)
        {
            bool prev = probing;
            probing = true;
            try
            {
                var c = model.GetColumnWithoutReservations(x, z);
                return new ColumnInfo(c.Top, c.Elev, IsBlocked(c));
            }
            finally
            {
                probing = prev;
            }
        }

        public static void Postfix(TerrainModel __instance, double x, double z, ref TerrainModel.Column __result)
        {
            if (probing) return;
            var sys = EarthTpBridgeModSystem.Active;
            if (sys == null) return;
            var engine = sys.EngineFor(__instance);
            if (engine == null) return;
            bool blocked = IsBlocked(__result);
            if (blocked) return;
            int oldTop = __result.Top;
            int newTop = engine.AdjustTop((int)Math.Floor(x), (int)Math.Floor(z), new ColumnInfo(oldTop, __result.Elev, false));
            if (newTop == oldTop) return;
            if (__result.WaterTop == oldTop) __result.WaterTop = newTop;
            __result.Top = newTop;
        }
    }
}
