namespace EarthTpBridge.Core
{
    /// <summary>Seeded 2D simplex noise (Gustavson's public-domain algorithm). Output about [-1, 1].</summary>
    public sealed class Simplex2D
    {
        static readonly int[] GradX = { 1, -1, 1, -1, 1, -1, 0, 0 };
        static readonly int[] GradY = { 1, 1, -1, -1, 0, 0, 1, -1 };
        const double F2 = 0.36602540378443865; // (sqrt(3)-1)/2
        const double G2 = 0.21132486540518713; // (3-sqrt(3))/6

        readonly byte[] perm = new byte[512];

        public Simplex2D(long seed)
        {
            var p = new byte[256];
            for (int i = 0; i < 256; i++) p[i] = (byte)i;
            for (int i = 255; i > 0; i--)
            {
                int j = (int)(BridgeMath.Hash01(i, 7919, seed) * (i + 1));
                (p[i], p[j]) = (p[j], p[i]);
            }
            for (int i = 0; i < 512; i++) perm[i] = p[i & 255];
        }

        static int FastFloor(double x) => x >= 0 ? (int)x : (int)x - 1;

        double Corner(int gi, double x, double y)
        {
            double t = 0.5 - x * x - y * y;
            if (t < 0) return 0;
            t *= t;
            return t * t * (GradX[gi] * x + GradY[gi] * y);
        }

        public double Noise(double xin, double yin)
        {
            double s = (xin + yin) * F2;
            int i = FastFloor(xin + s);
            int j = FastFloor(yin + s);
            double t = (i + j) * G2;
            double x0 = xin - (i - t);
            double y0 = yin - (j - t);
            int i1 = x0 > y0 ? 1 : 0;
            int j1 = 1 - i1;
            double x1 = x0 - i1 + G2, y1 = y0 - j1 + G2;
            double x2 = x0 - 1 + 2 * G2, y2 = y0 - 1 + 2 * G2;
            int ii = i & 255, jj = j & 255;
            int g0 = perm[ii + perm[jj]] & 7;
            int g1 = perm[ii + i1 + perm[jj + j1]] & 7;
            int g2 = perm[ii + 1 + perm[jj + 1]] & 7;
            return 70.0 * (Corner(g0, x0, y0) + Corner(g1, x1, y1) + Corner(g2, x2, y2));
        }
    }
}
