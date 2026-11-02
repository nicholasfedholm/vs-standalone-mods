using System;
using System.Collections.Generic;
using EarthTpBridge.Core;
using Xunit;

namespace EarthTpBridge.Tests
{
    public class EngineTests
    {
        const int Sea = 128, MapY = 512;

        static List<LandformDef> Defs() => new()
        {
            new LandformDef { Code = "flat", MinHeight = 0.0, MaxHeight = 0.15, Weight = 1, Octaves = new double[] { 1, 1, 1, 0, 0.3, 0, 0.1, 0, 0 } },
            new LandformDef { Code = "hills", MinHeight = 0.15, MaxHeight = 0.5, Weight = 2, Octaves = new double[] { 1, 0, 0, 0, 0.5, 0.2, 0.1, 0.05, 0.02 } },
            new LandformDef { Code = "mtn", MinHeight = 0.5, MaxHeight = 1.0, Weight = 1, Octaves = new double[] { 0, 0, 0, 0.6, 0.4, 0.3, 0.2, 0.1, 0.05 } },
        };

        // Fake Earth: river along z = 0 (|z| <= 2), sea for x < -200, land elevation rising with x.
        static ColumnInfo FakeEarth(int x, int z)
        {
            if (x < -200) return new ColumnInfo(Sea - 10, -100, true);
            double elev = 50 + Math.Max(0, x) * 2 + 80 * Math.Sin(z * 0.01);
            int top = Sea + 2 + (int)(40 * Math.Log(1 + elev / 200));
            bool river = Math.Abs(z) <= 2;
            return new ColumnInfo(top, elev, river);
        }

        static BridgeEngine Engine(BridgeConfig? cfg = null) =>
            new(cfg ?? new BridgeConfig(), Defs(), 987654321L, MapY, Sea, h => 40 / (200 + Math.Max(0, h)), FakeEarth);

        [Fact]
        public void DetailOctaves_DropContinentScale()
        {
            var o = Defs()[0].DetailOctaves();
            Assert.Equal(new double[] { 0, 0, 0, 0, 0.3, 0, 0.1, 0, 0 }, o);
            Assert.Equal(1, Defs()[0].Octaves[0]);
        }

        [Fact]
        public void Picker_RespectsWindowsAndFallsBackToNearest()
        {
            var d = Defs();
            Assert.Equal(0, LandformPicker.Pick(d, 0.1, 0.5));
            Assert.Equal(2, LandformPicker.Pick(d, 0.8, 0.99));
            Assert.Equal(-1, LandformPicker.Pick(new List<LandformDef>(), 0.5, 0.5));
            var gap = new List<LandformDef> { new() { MinHeight = 0, MaxHeight = 0.1 }, new() { MinHeight = 0.6, MaxHeight = 0.9 } };
            Assert.Equal(1, LandformPicker.Pick(gap, 0.5, 0.3));
            Assert.Equal(0, LandformPicker.Pick(gap, 0.2, 0.3));
        }

        [Fact]
        public void Picker_WeightsAreHonoured()
        {
            var d = new List<LandformDef> { new() { MinHeight = 0, MaxHeight = 1, Weight = 1 }, new() { MinHeight = 0, MaxHeight = 1, Weight = 3 } };
            int second = 0;
            for (int i = 0; i < 4000; i++) if (LandformPicker.Pick(d, 0.5, BridgeMath.Hash01(i, 0, 9)) == 1) second++;
            Assert.InRange(second / 4000.0, 0.70, 0.80);
        }

        [Fact]
        public void RiverAndNearRiverColumnsKeepEarthHeight()
        {
            var e = Engine();
            for (int x = 0; x < 400; x += 7)
            {
                for (int z = -2; z <= 2; z++)
                {
                    var c = FakeEarth(x, z);
                    Assert.Equal(c.Top, e.AdjustTop(x, z, c));
                }
                // lattice fade: within the lattice spacing of the river the mask is zero
                Assert.Equal(0, e.WaterMask(x, 4), 9);
            }
        }

        [Fact]
        public void MaskRampsMonotonicallyAwayFromRiver()
        {
            var e = Engine();
            double prev = -1;
            for (int z = 4; z <= 40; z += 4)
            {
                double m = e.WaterMask(100, z);
                Assert.True(m >= prev - 1e-12, $"mask dropped at z={z}");
                prev = m;
            }
            Assert.Equal(1, e.WaterMask(100, 40), 9);
        }

        [Fact]
        public void DetailIsBoundedNonZeroAndDeterministic()
        {
            var e1 = Engine();
            var e2 = Engine();
            int changed = 0, n = 0, maxAbs = 0;
            for (int x = 0; x < 2000; x += 13)
                for (int z = 60; z < 2000; z += 17)
                {
                    var c = FakeEarth(x, z);
                    int t = e1.AdjustTop(x, z, c);
                    Assert.Equal(t, e2.AdjustTop(x, z, c));
                    if (c.Top <= Sea) Assert.Equal(c.Top, t);
                    else Assert.True(t > Sea, "land pushed to sea level");
                    int d = Math.Abs(t - c.Top);
                    Assert.True(d <= 24);
                    maxAbs = Math.Max(maxAbs, d);
                    if (d > 0) changed++;
                    n++;
                }
            Assert.True(changed > n / 4, $"only {changed}/{n} columns changed");
            Assert.True(maxAbs >= 2, $"max offset {maxAbs}");
        }

        [Fact]
        public void StrengthZeroIsIdentityAndStrengthScales()
        {
            var off = Engine(new BridgeConfig { Strength = 0 });
            var full = Engine(new BridgeConfig { Strength = 1, MaxOffsetBlocks = 1000 });
            var dbl = Engine(new BridgeConfig { Strength = 2, MaxOffsetBlocks = 1000 });
            double s1 = 0, s2 = 0;
            for (int x = 0; x < 1500; x += 11)
                for (int z = 80; z < 1500; z += 19)
                {
                    var c = FakeEarth(x, z);
                    Assert.Equal(c.Top, off.AdjustTop(x, z, c));
                    s1 += Math.Abs(full.AdjustTop(x, z, c) - c.Top);
                    s2 += Math.Abs(dbl.AdjustTop(x, z, c) - c.Top);
                }
            Assert.InRange(s2 / s1, 1.7, 2.3);
        }

        [Fact]
        public void HighElevationGetsLessDetailThanLowland()
        {
            var e = Engine(new BridgeConfig { MaxOffsetBlocks = 1000 });
            double sea0 = 40 / 200.0;
            Assert.True(BridgeMath.SlopeFactor(40 / 3200.0, sea0, 1, 0) < 0.07);
            // Same column top and noise, different elevation: amplitude must shrink with the log-curve slope.
            double low = 0, high = 0;
            for (int x = 0; x < 1000; x += 9)
                for (int z = 100; z < 1000; z += 23)
                {
                    int top = 200;
                    low += Math.Abs(e.AdjustTop(x, z, new ColumnInfo(top, 0, false)) - top);
                    high += Math.Abs(e.AdjustTop(x, z, new ColumnInfo(top, 3000, false)) - top);
                }
            Assert.True(high < low * 0.2, $"high {high} low {low}");
        }

        [Fact]
        public void SeaAndLowCoastUntouched()
        {
            var e = Engine();
            Assert.Equal(Sea - 10, e.AdjustTop(-300, 500, FakeEarth(-300, 500)));
            Assert.Equal(Sea + 1, e.AdjustTop(500, 500, new ColumnInfo(Sea + 1, 10, false)));
        }
    }
}
