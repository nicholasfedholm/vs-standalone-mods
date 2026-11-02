using System;
using System.Collections.Concurrent;
using System.Collections.Generic;

namespace EarthTpBridge.Core
{
    public class BridgeConfig
    {
        public bool Enabled = true;
        public bool StandDownTerraPrety = true;
        public double Strength = 1.0;
        public double EarthDetailScale = 0.6;
        public double SlopeExponent = 1.0;
        public double SlopeFloor = 0.0;
        public double RiverFadeBlocks = 16;
        public double CoastFadeBlocks = 6;
        public int MaxOffsetBlocks = 24;
    }

    /// <summary>A TP landform usable for detail: height window from landformheights.json, weight and octaves from landforms.json.</summary>
    public sealed class LandformDef
    {
        public string Code = "";
        public double MinHeight;
        public double MaxHeight = 1.0;
        public double Weight = 1.0;
        public double[] Octaves = Array.Empty<double>();

        /// <summary>Octaves 0-2 hold continent-scale shape; Earth owns that, so they are dropped (as mcleanlt Resize does).</summary>
        public double[] DetailOctaves()
        {
            var o = (double[])Octaves.Clone();
            for (int i = 0; i < Math.Min(3, o.Length); i++) o[i] = 0;
            return o;
        }
    }

    /// <summary>Raw Earth column facts the engine needs, read before the bridge changes anything.</summary>
    public readonly struct ColumnInfo
    {
        public readonly int Top;
        public readonly double Elev;
        public readonly bool Blocked;

        public ColumnInfo(int top, double elev, bool blocked)
        {
            Top = top;
            Elev = elev;
            Blocked = blocked;
        }
    }

    public static class LandformPicker
    {
        /// <summary>Weighted pick among rows whose window holds h; nearest window centre if none does. -1 if the list is empty.</summary>
        public static int Pick(IReadOnlyList<LandformDef> defs, double h, double rand01)
        {
            double total = 0;
            for (int i = 0; i < defs.Count; i++)
            {
                var d = defs[i];
                if (d.Weight > 0 && d.MinHeight <= h && h <= d.MaxHeight) total += d.Weight;
            }
            if (total > 0)
            {
                double r = rand01 * total;
                int last = -1;
                for (int i = 0; i < defs.Count; i++)
                {
                    var d = defs[i];
                    if (!(d.Weight > 0 && d.MinHeight <= h && h <= d.MaxHeight)) continue;
                    last = i;
                    r -= d.Weight;
                    if (r < 0) return i;
                }
                return last;
            }
            int best = -1;
            double bestDist = double.MaxValue;
            for (int i = 0; i < defs.Count; i++)
            {
                double dist = Math.Abs((defs[i].MinHeight + defs[i].MaxHeight) / 2 - h);
                if (dist < bestDist)
                {
                    bestDist = dist;
                    best = i;
                }
            }
            return best;
        }
    }

    /// <summary>
    /// Computes the bridge's adjusted surface Y for one Earth column. Thread safe; caches are pure memos of
    /// position-only values, so clearing them never changes output.
    /// </summary>
    public sealed class BridgeEngine
    {
        public const int LatticeSpacing = 4;
        public const int PickCell = 64;
        const int MaxCacheEntries = 1 << 21;

        readonly BridgeConfig cfg;
        readonly IReadOnlyList<LandformDef> defs;
        readonly double[][] detailOctaves;
        readonly double[] bands;
        readonly long seed;
        readonly int mapSizeY;
        readonly int seaLevel;
        readonly Func<double, double> slope;
        readonly Func<int, int, ColumnInfo> probe;
        readonly Simplex2D simplex;
        readonly double f0;

        readonly ConcurrentDictionary<long, bool> blockedCache = new();
        readonly ConcurrentDictionary<long, double> latticeMaskCache = new();
        readonly ConcurrentDictionary<long, int> cellCache = new();

        /// <param name="slope">Earth's dY/dh at elevation h (VerticalScale.Slope).</param>
        /// <param name="probe">Raw Earth column at block x,z (must not include the bridge's own change).</param>
        public BridgeEngine(BridgeConfig cfg, IReadOnlyList<LandformDef> defs, long seed, int mapSizeY, int seaLevel,
            Func<double, double> slope, Func<int, int, ColumnInfo> probe)
        {
            this.cfg = cfg;
            this.defs = defs;
            this.seed = seed;
            this.mapSizeY = mapSizeY;
            this.seaLevel = seaLevel;
            this.slope = slope;
            this.probe = probe;
            simplex = new Simplex2D(seed ^ 0x5EED7E77A);
            f0 = 0.00030618621784789723 / Math.Max(1.0, mapSizeY / 256.0);
            detailOctaves = new double[defs.Count][];
            bands = new double[defs.Count];
            for (int i = 0; i < defs.Count; i++)
            {
                detailOctaves[i] = defs[i].DetailOctaves();
                bands[i] = BridgeMath.Band(defs[i].MinHeight, defs[i].MaxHeight, mapSizeY);
            }
        }

        static long Key(int a, int b) => ((long)a << 32) ^ (uint)b;

        static void Bound<T>(ConcurrentDictionary<long, T> d)
        {
            if (d.Count > MaxCacheEntries) d.Clear();
        }

        /// <summary>Normalised fractal noise for one landform, about [-1, 1].</summary>
        public double ShapeNoise(int defIndex, double x, double z)
        {
            double[] oct = detailOctaves[defIndex];
            double sum = 0, wsum = 0, f = f0;
            for (int k = 0; k < oct.Length; k++, f *= 2)
            {
                double a = oct[k];
                if (a <= 0) continue;
                sum += a * simplex.Noise(x * f + 1000.5 + k * 4099.3, z * f + 1000.5 + k * 2741.9);
                wsum += a;
            }
            return wsum > 0 ? sum / wsum : 0;
        }

        /// <summary>Landform index of a pick cell, -1 for an all-sea cell.</summary>
        public int CellLandform(int cx, int cz)
        {
            long key = Key(cx, cz);
            if (cellCache.TryGetValue(key, out int v)) return v;
            var elevs = new List<double>(25);
            int bx = cx * PickCell + PickCell / 2, bz = cz * PickCell + PickCell / 2;
            for (int i = -2; i <= 2; i++)
                for (int j = -2; j <= 2; j++)
                    elevs.Add(probe(bx + i * 16, bz + j * 16).Elev);
            double rough = BridgeMath.Roughness(elevs, out double mean, out int land);
            v = land == 0 || defs.Count == 0
                ? -1
                : LandformPicker.Pick(defs, BridgeMath.Ladder(rough, mean), BridgeMath.Hash01(cx, cz, seed));
            Bound(cellCache);
            cellCache[key] = v;
            return v;
        }

        /// <summary>band/2 * shape noise, bilinearly blended over the four nearest pick cells.</summary>
        public double HalfBandNoise(int x, int z)
        {
            double u = (x + 0.5) / PickCell - 0.5, w = (z + 0.5) / PickCell - 0.5;
            int c0 = (int)Math.Floor(u), r0 = (int)Math.Floor(w);
            double tu = u - c0, tw = w - r0;
            double acc = 0;
            for (int a = 0; a <= 1; a++)
                for (int b = 0; b <= 1; b++)
                {
                    double wt = (a == 0 ? 1 - tu : tu) * (b == 0 ? 1 - tw : tw);
                    if (wt <= 0) continue;
                    int li = CellLandform(c0 + a, r0 + b);
                    if (li < 0) continue;
                    acc += wt * 0.5 * bands[li] * ShapeNoise(li, x, z);
                }
            return acc;
        }

        bool LatticeBlocked(int lx, int lz)
        {
            long key = Key(lx, lz);
            if (blockedCache.TryGetValue(key, out bool b)) return b;
            b = probe(lx * LatticeSpacing, lz * LatticeSpacing).Blocked;
            Bound(blockedCache);
            blockedCache[key] = b;
            return b;
        }

        public double LatticeMask(int lx, int lz)
        {
            long key = Key(lx, lz);
            if (latticeMaskCache.TryGetValue(key, out double m)) return m;
            double reach = cfg.RiverFadeBlocks + LatticeSpacing;
            int r = (int)Math.Ceiling(reach / LatticeSpacing);
            double best = double.PositiveInfinity;
            for (int i = -r; i <= r; i++)
                for (int j = -r; j <= r; j++)
                {
                    double d = LatticeSpacing * Math.Sqrt(i * i + j * j);
                    if (d > reach || d >= best) continue;
                    if (LatticeBlocked(lx + i, lz + j)) best = d;
                }
            m = BridgeMath.LatticePointMask(best, LatticeSpacing, cfg.RiverFadeBlocks);
            Bound(latticeMaskCache);
            latticeMaskCache[key] = m;
            return m;
        }

        /// <summary>River, lake, sea and beach fade for a column, bilinear over the lattice.</summary>
        public double WaterMask(int x, int z)
        {
            int lx = (int)Math.Floor((double)x / LatticeSpacing), lz = (int)Math.Floor((double)z / LatticeSpacing);
            double tx = (x - lx * LatticeSpacing) / (double)LatticeSpacing;
            double tz = (z - lz * LatticeSpacing) / (double)LatticeSpacing;
            double m00 = LatticeMask(lx, lz), m10 = LatticeMask(lx + 1, lz);
            double m01 = LatticeMask(lx, lz + 1), m11 = LatticeMask(lx + 1, lz + 1);
            return (m00 * (1 - tx) + m10 * tx) * (1 - tz) + (m01 * (1 - tx) + m11 * tx) * tz;
        }

        /// <summary>The adjusted Top for a raw Earth column. Blocked columns are returned unchanged.</summary>
        public int AdjustTop(int x, int z, in ColumnInfo c)
        {
            if (c.Blocked || c.Top <= seaLevel) return c.Top;
            double coast = BridgeMath.CoastMask(c.Top, seaLevel, cfg.CoastFadeBlocks);
            if (coast <= 0) return c.Top;
            double mask = coast * WaterMask(x, z);
            if (mask <= 0) return c.Top;
            double sf = BridgeMath.SlopeFactor(slope(Math.Max(0, c.Elev)), slope(0), cfg.SlopeExponent, cfg.SlopeFloor);
            int off = BridgeMath.Offset(cfg.Strength, HalfBandNoise(x, z), sf, mask, cfg.MaxOffsetBlocks);
            return BridgeMath.ApplyOffset(c.Top, off, seaLevel, mapSizeY);
        }
    }
}
