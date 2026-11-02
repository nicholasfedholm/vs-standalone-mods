using System;
using System.Collections.Generic;
using EarthRealms.Shared;
using Vintagestory.API.Common;
using Vintagestory.API.Common.Entities;
using Vintagestory.API.MathTools;
using Vintagestory.API.Server;

namespace EarthFlagships
{
    /// <summary>
    /// Earth Flagships: region-locks six LoP dinosaur families to their fossil
    /// home regions, Earth worlds only.
    ///
    /// Mechanism: the veto sits on IServerEventAPI.OnTrySpawnEntity, the game's
    /// natural-spawn attempt event. Both natural spawn paths call it
    /// (GenCreatures worldgen spawning and the runtime EntitySpawnerResult),
    /// and no other path does: breeding, hatching player-placed eggs, chunk
    /// load restores and commands all call SpawnEntity directly. So gated
    /// animals can never be removed once they exist, and tamed/bred/placed
    /// stock is unreachable by construction.
    ///
    /// The Earth gate is the same read Earth Worldgen's own shims use:
    /// SaveGame.WorldConfiguration "earthWorldgen". In any other world this
    /// mod is a complete no-op.
    /// </summary>
    public class EarthFlagshipsModSystem : ModSystem
    {
        private ICoreServerAPI sapi;
        private FlagshipConfig config;
        private bool? earthWorld;          // null = not yet readable
        private int mapSizeX, mapSizeZ;
        private readonly HashSet<string> loggedBlocks = new HashSet<string>();
        private int blockedCount;

        public override bool ShouldLoad(EnumAppSide side) => side == EnumAppSide.Server;

        public override void StartServerSide(ICoreServerAPI api)
        {
            sapi = api;
            config = api.LoadModConfig<FlagshipConfig>("earthflagships.json");
            if (config == null)
            {
                config = new FlagshipConfig();
                api.StoreModConfig(config, "earthflagships.json");
            }

            mapSizeX = api.WorldManager.MapSizeX;
            mapSizeZ = api.WorldManager.MapSizeZ;

            sapi.Event.OnTrySpawnEntity += OnTrySpawnEntity;
            sapi.Logger.Notification(
                "[earthflagships] loaded: {0} flagship variants across {1} families gated to their fossil regions (Earth worlds only).",
                FlagshipTable.Homes.Count, FlagshipTable.Families.Length);
        }

        private bool IsEarthWorld()
        {
            if (earthWorld.HasValue) return earthWorld.Value;
            try
            {
                var save = sapi.WorldManager.SaveGame;
                if (save?.WorldConfiguration == null) return false; // too early; retry on the next spawn
                earthWorld = save.WorldConfiguration.GetAsBool("earthWorldgen", false);
                if (earthWorld.Value)
                {
                    sapi.Logger.Notification(
                        "[earthflagships] Earth world detected (earthWorldgen=true), map {0} x {1}: flagship gate ACTIVE.",
                        mapSizeX, mapSizeZ);
                }
                return earthWorld.Value;
            }
            catch
            {
                return false;
            }
        }

        private bool OnTrySpawnEntity(IBlockAccessor blockAccessor, ref EntityProperties properties, Vec3d spawnPosition, long herdId)
        {
            // Fast path: not a flagship family -> allow without touching anything else.
            string family = FlagshipTable.FamilyOfCodePath(properties?.Code?.Path);
            if (family == null) return true;
            if (config == null || !config.Enabled) return true;
            if (!config.FamilyEnabled(family)) return true;

            string variant = null;
            properties.Variant?.TryGetValue("type", out variant);
            if (variant == null) return true;
            if (!FlagshipTable.TryGetHomes(family, variant, out _)) return true; // unknown variant: fail open

            if (!IsEarthWorld()) return true; // standard worlds: complete no-op

            double lat = EarthCoords.LatitudeAt(spawnPosition.Z, mapSizeZ);
            double lon = EarthCoords.LongitudeAt(spawnPosition.X, mapSizeX);

            var verdict = FlagshipGate.Decide(
                earthWorld: true,
                masterEnabled: true,
                familyEnabled: null, // already checked above
                family: family,
                typeVariant: variant,
                lat: lat,
                lon: lon);

            if (verdict == GateVerdict.Block)
            {
                blockedCount++;
                if (config.LogFirstBlockPerVariant && loggedBlocks.Add(family + ":" + variant))
                {
                    sapi.Logger.Notification(
                        "[earthflagships] blocked natural spawn of {0} ({1}) at lat {2:F1}, lon {3:F1}: outside its home region(s) {4}.",
                        variant, family, lat, lon,
                        string.Join(", ", FlagshipTable.Homes[(family, variant)]));
                }
                else
                {
                    sapi.Logger.Debug("[earthflagships] blocked {0}:{1} at lat {2:F1}, lon {3:F1} (total blocked: {4})",
                        family, variant, lat, lon, blockedCount);
                }
                return false;
            }
            return true;
        }
    }
}
