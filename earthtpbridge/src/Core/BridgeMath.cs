using System;
using System.Collections.Generic;

namespace EarthTpBridge.Core
{
    /// <summary>Pure math for the bridge. No game types, so it is unit tested directly.</summary>
    public static class BridgeMath
    {
        // mcleanlt TerraPretyLandforms.cs:78-80 roughness ladder (metres to TP height fraction)
        static readonly double[] LadderM = { 0, 60, 200, 500, 1200, 3000 };
        static readonly double[] LadderH = { 0, 0.15, 0.25, 0.45, 0.65, 1.0 };

        // mcleanlt TerraPretyLandforms.cs:320 BandFor over ReliefClass.Band
        static readonly double[] BandX = { 0.075, 0.2, 0.35, 0.55, 0.825 };
        static readonly double[] BandY = { 4, 9, 16, 26, 40 };

        public static double Clamp01(double t) => t < 0 ? 0 : (t > 1 ? 1 : t);

        public static double SmoothStep(double t)
        {
            t = Clamp01(t);
            return t * t * (3 - 2 * t);
        }

        static double Piecewise(double[] xs, double[] ys, double x)
        {
            if (x <= xs[0]) return ys[0];
            for (int i = 1; i < xs.Length; i++)
            {
                if (x <= xs[i]) return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
            }
            return ys[ys.Length - 1];
        }

        /// <summary>TP height fraction for a roughness in metres; lowland floor 0.075 when the land is above 30 m.</summary>
        public static double Ladder(double roughnessM, double meanElevM)
        {
            double h = Piecewise(LadderM, LadderH, roughnessM);
            if (meanElevM > 30) h = Math.Max(h, 0.075);
            return h;
        }

        public static double BandFor(double height) => Piecewise(BandX, BandY, height);

        /// <summary>TP vertical band in blocks for a landform height window (mcleanlt :176).</summary>
        public static double Band(double minHeight, double maxHeight, int mapSizeY)
            => BandFor((minHeight + maxHeight) / 2) * (mapSizeY / 256.0) * 1.5;

        /// <summary>Slope of Earth's log curve s*ln(1+h/LandH0) relative to its slope at sea level: LandH0/(LandH0+h).</summary>
        public static double LogSlopeRatio(double elevM, double landH0)
            => landH0 / (landH0 + Math.Max(0, elevM));

        /// <summary>Amplitude factor from a slope ratio, raised to exponent and kept in [floor, 1].</summary>
        public static double SlopeFactor(double slopeAtH, double slopeAt0, double exponent, double floor)
        {
            if (!(slopeAt0 > 0)) return 1;
            double r = Math.Min(1, Math.Max(0, slopeAtH / slopeAt0));
            r = Math.Pow(r, exponent);
            return Math.Min(1, Math.Max(Math.Min(floor, 1), r));
        }

        /// <summary>0 at or just above sea level, ramping to 1 over fadeBlocks.</summary>
        public static double CoastMask(int top, int seaLevel, double fadeBlocks)
        {
            if (fadeBlocks <= 0) return top > seaLevel ? 1 : 0;
            return SmoothStep((top - seaLevel - 1) / fadeBlocks);
        }

        /// <summary>Mask at a lattice point from the distance (blocks) to the nearest blocked lattice point.</summary>
        public static double LatticePointMask(double nearestBlockedDist, double spacing, double fadeBlocks)
        {
            if (double.IsPositiveInfinity(nearestBlockedDist)) return 1;
            if (fadeBlocks <= 0) return nearestBlockedDist > spacing ? 1 : 0;
            return SmoothStep((nearestBlockedDist - spacing) / fadeBlocks);
        }

        /// <summary>3 * standard deviation of land samples (elev > 0), as in mcleanlt EarthLandformLayer.SmoothRoughness.</summary>
        public static double Roughness(IReadOnlyList<double> elevs, out double meanLand, out int landCount)
        {
            double sum = 0, sq = 0;
            landCount = 0;
            foreach (double e in elevs)
            {
                if (e <= 0) continue;
                sum += e;
                sq += e * e;
                landCount++;
            }
            if (landCount == 0)
            {
                meanLand = 0;
                return 0;
            }
            meanLand = sum / landCount;
            double var = Math.Max(0, sq / landCount - meanLand * meanLand);
            return 3 * Math.Sqrt(var);
        }

        /// <summary>Final offset in blocks: strength * band/2 * noise * slope * mask, capped.</summary>
        public static int Offset(double strength, double halfBandNoise, double slopeFactor, double mask, int maxOffset)
        {
            double dy = strength * halfBandNoise * slopeFactor * mask;
            int off = (int)Math.Round(dy);
            return Math.Max(-maxOffset, Math.Min(maxOffset, off));
        }

        /// <summary>Apply an offset; land never drops to sea level, and stays inside Earth's 1..mapSizeY-2 clamp.</summary>
        public static int ApplyOffset(int top, int offset, int seaLevel, int mapSizeY)
        {
            int nt = top + offset;
            if (top > seaLevel) nt = Math.Max(nt, seaLevel + 1);
            return Math.Max(1, Math.Min(mapSizeY - 2, nt));
        }

        /// <summary>Deterministic hash of two ints and a seed to [0,1).</summary>
        public static double Hash01(long a, long b, long seed)
        {
            ulong x = (ulong)seed ^ ((ulong)a * 0x9E3779B97F4A7C15UL) ^ ((ulong)b * 0xC2B2AE3D27D4EB4FUL);
            x ^= x >> 30; x *= 0xBF58476D1CE4E5B9UL;
            x ^= x >> 27; x *= 0x94D049BB133111EBUL;
            x ^= x >> 31;
            return (x >> 11) * (1.0 / (1UL << 53));
        }
    }
}
