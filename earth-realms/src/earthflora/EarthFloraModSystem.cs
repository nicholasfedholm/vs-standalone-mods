using System;
using System.Collections.Generic;
using System.Linq;
using EarthRealms.Shared;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.API.Server;
using Vintagestory.ServerMods;
using Vintagestory.ServerMods.NoObf;

namespace EarthFlora
{
    /// <summary>Shape of a Floral Zones pack's config/biomes.json (the packs' own tables).</summary>
    public class PackBiomesJson
    {
        public Dictionary<string, List<string>> TreeBiomes { get; set; }
        public Dictionary<string, List<string>> BlockPatchBiomes { get; set; }
    }

    /// <summary>
    /// Earth Flora Realms: keeps Floral Zones plants in their home floristic
    /// regions, Earth worlds only.
    ///
    /// The species-to-realm assignments are copied verbatim from the packs' own
    /// config/biomes.json tables. What the packs never had is the other half of
    /// the Biomes system: which realm a position belongs to. Here the realm of
    /// a position comes from generous lat/lon boxes drawn on the real Earth
    /// (EarthRealms.Shared.Realms), via the Earth mod's own block/lat-lon map.
    ///
    /// Enforcement, two official-or-verified surfaces:
    ///  - Block patches: this class is an IBlockPatchModifier registered with
    ///    GenVegetationAndPatches; per chunk it supplies a copy of the game's
    ///    patch list with out-of-realm species filtered out.
    ///  - Trees and shrubs: WgenTreeSupplier.GetRandomGenForClimate chooses a
    ///    tree type from climate alone (no position), so a Harmony prefix
    ///    narrows its candidate list to the variants allowed in the current
    ///    chunk's realm. The current chunk is tracked through a Harmony hook
    ///    on GenVegetationAndPatches.OnChunkColumnGen (ThreadLocal). If either
    ///    patch target is missing, tree gating disables itself with an error
    ///    log instead of silently doing nothing.
    ///
    /// In any world whose config does not set earthWorldgen=true, every entry
    /// point returns "allow / pass through": a complete no-op.
    /// </summary>
    public class EarthFloraModSystem : ModSystem, IBlockPatchModifier
    {
        internal static EarthFloraModSystem Instance { get; private set; }

        private ICoreServerAPI sapi;
        private FloraConfig config;
        private FloraAssignments assignments;
        private bool? earthWorld;
        private int mapSizeX, mapSizeZ;
        private Harmony harmony;
        private bool treesActive;
        private readonly Dictionary<string, BlockPatch[]> filteredCache = new Dictionary<string, BlockPatch[]>();

        public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

        public override double ExecuteOrder() => 0.6;

        internal bool GateActive => config != null && config.Enabled && IsEarthWorld() && assignments != null;

        public override void StartServerSide(ICoreServerAPI api)
        {
            sapi = api;
            Instance = this;

            config = api.LoadModConfig<FloraConfig>("earthflora.json");
            if (config == null)
            {
                config = new FloraConfig();
                api.StoreModConfig(config, "earthflora.json");
            }

            mapSizeX = api.WorldManager.MapSizeX;
            mapSizeZ = api.WorldManager.MapSizeZ;

            assignments = LoadPackTables(api);

            if (config.GateBlockPatches)
            {
                var veg = api.ModLoader.GetModSystem<GenVegetationAndPatches>();
                if (veg != null)
                {
                    veg.RegisterPatchModifier(this);
                    sapi.Logger.Notification("[earthflora] block patch realm filter registered.");
                }
                else
                {
                    sapi.Logger.Error("[earthflora] GenVegetationAndPatches not found: block patch gating INERT.");
                }
            }

            if (config.GateTrees)
            {
                treesActive = EarthFloraTreeGate.ApplyPatches(api, out string error);
                if (!treesActive)
                {
                    sapi.Logger.Error("[earthflora] tree realm gating INERT: {0}", error);
                }
            }
        }

        public override void Dispose()
        {
            if (harmony != null)
            {
                harmony.UnpatchAll("earthflora.realmgate");
                harmony = null;
            }
            if (Instance == this) Instance = null;
            base.Dispose();
        }

        internal void SetHarmony(Harmony h) => harmony = h;
        internal bool TreesActive => treesActive;

        private FloraAssignments LoadPackTables(ICoreServerAPI api)
        {
            var result = new FloraAssignments();
            try
            {
                var assets = api.Assets.GetMany("config/biomes.json");
                foreach (var asset in assets)
                {
                    string domain = asset.Location.Domain;
                    if (!domain.StartsWith("floralzones")) continue;
                    var parsed = asset.ToObject<PackBiomesJson>();
                    if (parsed == null) continue;
                    var table = new PackFloraTable
                    {
                        Domain = domain,
                        TreeBiomes = parsed.TreeBiomes ?? new Dictionary<string, List<string>>(),
                        BlockPatchBiomes = parsed.BlockPatchBiomes ?? new Dictionary<string, List<string>>()
                    };
                    result.AddPack(table);
                    sapi.Logger.Notification(
                        "[earthflora] copied realm tables from {0}: {1} tree species, {2} patch species.",
                        domain, table.TreeBiomes.Count, table.BlockPatchBiomes.Count);
                }
            }
            catch (Exception ex)
            {
                sapi.Logger.Error("[earthflora] failed to read pack realm tables: {0}", ex.Message);
            }
            sapi.Logger.Notification(
                "[earthflora] realm tables loaded: {0} packs, {1} tree species, {2} patch species.",
                result.PackCount, result.TreeSpeciesCount, result.PatchSpeciesCount);
            return result;
        }

        internal bool IsEarthWorld()
        {
            if (earthWorld.HasValue) return earthWorld.Value;
            try
            {
                var save = sapi.WorldManager.SaveGame;
                if (save?.WorldConfiguration == null) return false;
                earthWorld = save.WorldConfiguration.GetAsBool("earthWorldgen", false);
                if (earthWorld.Value)
                {
                    sapi.Logger.Notification(
                        "[earthflora] Earth world detected (earthWorldgen=true), map {0} x {1}: flora realm gate ACTIVE.",
                        mapSizeX, mapSizeZ);
                }
                return earthWorld.Value;
            }
            catch
            {
                return false;
            }
        }

        internal string RealmForChunk(int chunkX, int chunkZ)
        {
            double bx = chunkX * 32 + 16;
            double bz = chunkZ * 32 + 16;
            return Realms.RealmAtBlock(bx, bz, mapSizeX, mapSizeZ);
        }

        internal bool TreeAllowedHere(string generatorDomain, string generatorCodePath, string realm)
            => assignments != null && assignments.TreeAllowed(generatorDomain, generatorCodePath, realm);

        // ---- IBlockPatchModifier -------------------------------------------

        public bool PreventPlacementAt(int x, int z, int category) => false; // species veto lives in the provider filter

        public bool PreventPlacementBroadlyAt(int chunkX, int chunkZ) => false;

        public BlockPatchConfig GetPatchProviderAt(int chunkX, int chunkZ, ref EnumHandling handling)
        {
            if (config == null || !config.GateBlockPatches || !GateActive) return null;

            var veg = sapi.ModLoader.GetModSystem<GenVegetationAndPatches>();
            var source = veg?.bpc?.PatchesNonTree;
            if (source == null) return null; // game config not loaded yet: pass through

            string realm = RealmForChunk(chunkX, chunkZ);
            string key = realm ?? "<none>";
            if (!filteredCache.TryGetValue(key, out var filtered))
            {
                var kept = new List<BlockPatch>();
                foreach (var patch in source)
                {
                    var codes = patch.blockCodes?.Select(c => (c.Domain, c.Path)).ToArray();
                    if (codes == null || codes.Length == 0 || assignments.PatchAllowed(codes, realm))
                    {
                        kept.Add(patch);
                    }
                }
                filtered = kept.ToArray();
                filteredCache[key] = filtered;
            }

            handling = EnumHandling.PreventSubsequent;
            return new BlockPatchConfig
            {
                ChanceMultiplier = veg.bpc.ChanceMultiplier,
                Patches = filtered,
                PatchesNonTree = filtered
            };
        }
    }
}
