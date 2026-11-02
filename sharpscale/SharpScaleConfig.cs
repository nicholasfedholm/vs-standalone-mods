namespace SharpScale;

public class SharpScaleConfig
{
    public const string FileName = "sharpscale.json";
    public bool Enabled = true;
    /// <summary>0 = bilinear only, 1 = bilinear + CAS sharpening, 2 = FSR1 (EASU + RCAS).</summary>
    public int Mode = 2;
    /// <summary>0..1, drives the Mode 1 CAS strength.</summary>
    public float Sharpness = 0.5f;
    /// <summary>0..2 stops of RCAS attenuation (Mode 2). 0 = sharpest.</summary>
    public float RcasStops = 0.2f;
}
