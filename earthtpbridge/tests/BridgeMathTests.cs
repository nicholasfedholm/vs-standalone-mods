using System;
using System.Collections.Generic;
using EarthTpBridge.Core;
using Xunit;

namespace EarthTpBridge.Tests
{
    public class BridgeMathTests
    {
        [Fact]
        public void LogSlopeRatio_IsOneAtSeaAndHalvesAtLandH0()
        {
            Assert.Equal(1.0, BridgeMath.LogSlopeRatio(0, 200), 12);
            Assert.Equal(0.5, BridgeMath.LogSlopeRatio(200, 200), 12);
            Assert.Equal(200.0 / 3200.0, BridgeMath.LogSlopeRatio(3000, 200), 12);
            Assert.Equal(1.0, BridgeMath.LogSlopeRatio(-50, 200), 12);
        }

        [Fact]
        public void LogSlopeRatio_MatchesNumericDerivativeOfEarthCurve()
        {
            // Earth VerticalScale.Y: s * ln(1 + h / LandH0)
            double s = 40, h0 = 200;
            Func<double, double> y = h => s * Math.Log(1 + h / h0);
            foreach (double h in new[] { 0.0, 100, 1000, 5000 })
            {
                double num = (y(h + 1e-3) - y(h - 1e-3)) / 2e-3;
                double num0 = (y(1e-3) - y(0)) / 1e-3;
                Assert.Equal(BridgeMath.LogSlopeRatio(h, h0), num / num0, 3);
            }
        }

        [Fact]
        public void SlopeFactor_ExponentAndFloor()
        {
            Assert.Equal(0.25, BridgeMath.SlopeFactor(0.25, 1, 1, 0), 12);
            Assert.Equal(0.5, BridgeMath.SlopeFactor(0.25, 1, 0.5, 0), 12);
            Assert.Equal(0.4, BridgeMath.SlopeFactor(0.25, 1, 1, 0.4), 12);
            Assert.Equal(1.0, BridgeMath.SlopeFactor(2, 1, 1, 0), 12);
            Assert.Equal(1.0, BridgeMath.SlopeFactor(1, 0, 1, 0), 12);
        }

        [Fact]
        public void Ladder_MatchesMcleanltBreakpoints()
        {
            Assert.Equal(0.0, BridgeMath.Ladder(0, 0), 12);
            Assert.Equal(0.15, BridgeMath.Ladder(60, 0), 12);
            Assert.Equal(0.2, BridgeMath.Ladder(130, 0), 12);
            Assert.Equal(1.0, BridgeMath.Ladder(9000, 0), 12);
            Assert.Equal(0.075, BridgeMath.Ladder(0, 31), 12);
            Assert.Equal(0.15, BridgeMath.Ladder(60, 31), 12);
        }

        [Fact]
        public void BandFor_PiecewiseAndBandScalesWithMapHeight()
        {
            Assert.Equal(4, BridgeMath.BandFor(0.0), 12);
            Assert.Equal(9, BridgeMath.BandFor(0.2), 12);
            Assert.Equal(12.5, BridgeMath.BandFor(0.275), 12);
            Assert.Equal(40, BridgeMath.BandFor(0.9), 12);
            Assert.Equal(9 * 2 * 1.5, BridgeMath.Band(0.15, 0.25, 512), 12);
        }

        [Fact]
        public void CoastMask_ZeroAtSeaRampsToOne()
        {
            Assert.Equal(0, BridgeMath.CoastMask(110, 110, 6), 12);
            Assert.Equal(0, BridgeMath.CoastMask(111, 110, 6), 12);
            Assert.Equal(0.5, BridgeMath.CoastMask(114, 110, 6), 12);
            Assert.Equal(1, BridgeMath.CoastMask(117, 110, 6), 12);
            double prev = -1;
            for (int t = 105; t < 130; t++)
            {
                double m = BridgeMath.CoastMask(t, 110, 6);
                Assert.True(m >= prev);
                prev = m;
            }
        }

        [Fact]
        public void LatticePointMask_ZeroNearWaterOneFar()
        {
            Assert.Equal(0, BridgeMath.LatticePointMask(0, 4, 16), 12);
            Assert.Equal(0, BridgeMath.LatticePointMask(4, 4, 16), 12);
            Assert.Equal(0.5, BridgeMath.LatticePointMask(12, 4, 16), 12);
            Assert.Equal(1, BridgeMath.LatticePointMask(20, 4, 16), 12);
            Assert.Equal(1, BridgeMath.LatticePointMask(double.PositiveInfinity, 4, 16), 12);
        }

        [Fact]
        public void Roughness_IsThreeStdDevOfLand()
        {
            var e = new List<double> { -500, 100, 200, 300, -10 };
            double r = BridgeMath.Roughness(e, out double mean, out int land);
            Assert.Equal(3, land);
            Assert.Equal(200, mean, 9);
            Assert.Equal(3 * Math.Sqrt(20000.0 / 3), r, 6);
            Assert.Equal(0, BridgeMath.Roughness(new List<double> { -1, -2 }, out _, out int none));
            Assert.Equal(0, none);
        }

        [Fact]
        public void OffsetAndApply_CapAndKeepLandAboveSea()
        {
            Assert.Equal(24, BridgeMath.Offset(1, 100, 1, 1, 24));
            Assert.Equal(-24, BridgeMath.Offset(1, -100, 1, 1, 24));
            Assert.Equal(3, BridgeMath.Offset(1, 6, 0.5, 1, 24));
            Assert.Equal(0, BridgeMath.Offset(1, 6, 1, 0, 24));
            Assert.Equal(111, BridgeMath.ApplyOffset(113, -10, 110, 512));
            Assert.Equal(510, BridgeMath.ApplyOffset(505, 20, 110, 512));
            Assert.Equal(108, BridgeMath.ApplyOffset(105, 3, 110, 512));
        }

        [Fact]
        public void Hash01_DeterministicAndInRange()
        {
            for (int i = 0; i < 1000; i++)
            {
                double h = BridgeMath.Hash01(i, -i * 7, 12345);
                Assert.InRange(h, 0, 1 - 1e-15);
                Assert.Equal(h, BridgeMath.Hash01(i, -i * 7, 12345));
            }
            Assert.NotEqual(BridgeMath.Hash01(1, 2, 3), BridgeMath.Hash01(1, 2, 4));
        }

        [Fact]
        public void Simplex_BoundedDeterministicRoughlyZeroMean()
        {
            var a = new Simplex2D(42);
            var b = new Simplex2D(42);
            double sum = 0;
            int n = 0;
            for (int i = 0; i < 200; i++)
                for (int j = 0; j < 200; j++)
                {
                    double v = a.Noise(i * 0.137, j * 0.173);
                    Assert.InRange(v, -1.1, 1.1);
                    Assert.Equal(v, b.Noise(i * 0.137, j * 0.173));
                    sum += v;
                    n++;
                }
            Assert.InRange(sum / n, -0.05, 0.05);
            Assert.NotEqual(new Simplex2D(1).Noise(3.3, 4.4), new Simplex2D(2).Noise(3.3, 4.4));
        }
    }
}
