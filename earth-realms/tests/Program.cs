using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using EarthRealms.Shared;

// Offline verification for the earth-realms workstream.
// Usage: EarthRealms.Tests <ModsDir> <FixturesDir>
// Exit code 0 = all assertions passed.

int failures = 0;
int passed = 0;
void Check(bool cond, string label)
{
    if (cond) { passed++; Console.WriteLine("PASS  " + label); }
    else { failures++; Console.WriteLine("FAIL  " + label); }
}
void Eq(object actual, object expected, string label)
    => Check(Equals(actual, expected), $"{label} (expected: {expected ?? "null"}, got: {actual ?? "null"})");

string modsDir = args.Length > 0 ? args[0] : @"%APPDATA%\VintagestoryData\Mods";
string fixturesDir = args.Length > 1 ? args[1] : "fixtures";
const double QuarterX = 100352, QuarterZ = 50176;

// ---------- 1. EarthCoords + realm spot checks (REGIONS.md) ----------
Console.WriteLine("== realm spot checks ==");
(double lat, double lon, string realm)[] spots =
{
    (41.25, -95.93, Realms.AtlanticNearctic),     // Omaha
    (51.5, -0.12, Realms.AtlanticPalearctic),     // London
    (39.9, 116.4, Realms.EasternPalearctic),      // Beijing
    (35.7, 139.7, Realms.EasternPalearctic),      // Tokyo
    (-33.9, 151.2, Realms.Australasian),          // Sydney
    (-36.8, 174.8, Realms.Australasian),          // Auckland
    (-3.1, -60.0, Realms.AtlanticNeotropic),      // Manaus
    (-33.4, -70.7, Realms.PacificNeotropic),      // Santiago
    (6.5, 3.4, Realms.AtlanticAfrotropic),        // Lagos
    (-1.3, 36.8, Realms.EasternAfrotropic),       // Nairobi
    (-18.9, 47.5, Realms.EasternAfrotropic),      // Antananarivo (Madagascar box)
    (21.3, -157.8, Realms.Oceanic),               // Honolulu
    (0.0, -150.0, Realms.Oceanic),                // mid-Pacific
    (23.1, -82.4, Realms.AtlanticNeotropic),      // Havana (Caribbean exception box)
    (19.4, -99.1, Realms.AtlanticNeotropic),      // Mexico City (Central America box)
};
foreach (var (lat, lon, realm) in spots)
    Eq(Realms.RealmAt(lat, lon), realm, $"RealmAt({lat}, {lon})");
// Deliberate non-assert: northern Sweden (64.9, 19.9) resolves to atlantic
// palearctic by the boxes, because the sector split puts everything west of
// lon 45 in the atlantic box. That is the documented coarse edge of the
// sector logic, printed for the record instead of asserted.
Console.WriteLine($"INFO  RealmAt(64.9, 19.9) = {Realms.RealmAt(64.9, 19.9)} (Norrland: box edge, documented)");
Eq(Realms.RealmAt(-90, 0), null, "RealmAt(south pole) is null");
Eq(Realms.RealmAt(90, 0), null, "RealmAt(north pole) is null");

// Block round trip at Quarter size: Omaha lat/lon -> blocks -> realm.
double omahaBx = EarthCoords.BlockXOf(-95.93, QuarterX);
double omahaBz = EarthCoords.BlockZOf(41.25, QuarterZ);
Eq(Realms.RealmAtBlock(omahaBx, omahaBz, QuarterX, QuarterZ), Realms.AtlanticNearctic,
    "RealmAtBlock(Omaha blocks, Quarter)");
Check(Math.Abs(EarthCoords.LongitudeAt(omahaBx, QuarterX) - (-95.93)) < 0.01, "lon round trip");
Check(Math.Abs(EarthCoords.LatitudeAt(omahaBz, QuarterZ) - 41.25) < 0.01, "lat round trip");

// ---------- 2. Flagship gate decisions ----------
Console.WriteLine("== flagship gate ==");
GateVerdict Decide(bool earth, bool master, Func<string, bool> fam, string f, string v, double lat, double lon)
    => FlagshipGate.Decide(earth, master, fam, f, v, lat, lon);
Func<string, bool> allOn = _ => true;

Eq(Decide(true, true, allOn, "ceratopsidae", "triceratops", 47.5, -106.8), GateVerdict.Allow, "triceratops at Hell Creek allowed");
Eq(Decide(true, true, allOn, "ceratopsidae", "triceratops", 39.9, 116.4), GateVerdict.Block, "triceratops at Beijing blocked");
Eq(Decide(true, true, allOn, "tyrannosauridae", "tarbosaurus", 43.7, 101.0), GateVerdict.Allow, "tarbosaurus in Mongolia allowed");
Eq(Decide(true, true, allOn, "tyrannosauridae", "tarbosaurus", 47.5, -106.8), GateVerdict.Block, "tarbosaurus in Montana blocked");
Eq(Decide(true, true, allOn, "ceratopsidae", "sinoceratops", 37.0, 119.0), GateVerdict.Allow, "sinoceratops in Shandong allowed");
Eq(Decide(true, true, allOn, "ceratopsidae", "sinoceratops", 47.5, -106.8), GateVerdict.Block, "sinoceratops in Montana blocked");
Eq(Decide(true, true, allOn, "ceratopsidae", "protoceratops", 44.4, 103.7), GateVerdict.Allow, "protoceratops in the Gobi allowed");
Eq(Decide(true, true, allOn, "ceratopsidae", "ajkaceratops", 47.1, 17.6), GateVerdict.Allow, "ajkaceratops in Hungary allowed");
Eq(Decide(true, true, allOn, "spinosauridae", "spinosaurus", 28.3, 28.9), GateVerdict.Allow, "spinosaurus at Bahariya allowed");
Eq(Decide(true, true, allOn, "spinosauridae", "spinosaurus", -2.9, -44.3), GateVerdict.Block, "spinosaurus in Brazil blocked");
Eq(Decide(true, true, allOn, "spinosauridae", "oxalaia", -2.9, -44.3), GateVerdict.Allow, "oxalaia in NE Brazil allowed");
Eq(Decide(true, true, allOn, "spinosauridae", "ichthyovenator", 18.0, 104.0), GateVerdict.Allow, "ichthyovenator in Laos allowed");
Eq(Decide(true, true, allOn, "abelisauridae", "majungasaurus", -16.2, 46.9), GateVerdict.Allow, "majungasaurus in Madagascar allowed");
Eq(Decide(true, true, allOn, "abelisauridae", "majungasaurus", -38.7, -62.3), GateVerdict.Block, "majungasaurus in Argentina blocked");
Eq(Decide(true, true, allOn, "abelisauridae", "rajasaurus", 22.3, 73.2), GateVerdict.Allow, "rajasaurus in Gujarat allowed");
Eq(Decide(true, true, allOn, "carcharodontosauridae", "veterupristisaurus", -6.2, 35.1), GateVerdict.Allow, "veterupristisaurus in Tanzania allowed");
Eq(Decide(true, true, allOn, "herrerasauridae", "herrerasaurus", -30.1, -67.9), GateVerdict.Allow, "herrerasaurus at Ischigualasto allowed");
Eq(Decide(true, true, allOn, "herrerasauridae", "herrerasaurus", 41.25, -95.93), GateVerdict.Block, "herrerasaurus at Omaha blocked");

// The no-op and fail-open guarantees (the prompt's hard gates).
Eq(Decide(false, true, allOn, "ceratopsidae", "triceratops", 39.9, 116.4), GateVerdict.Allow, "standard world: no-op (triceratops at Beijing allowed)");
Eq(Decide(true, false, allOn, "ceratopsidae", "triceratops", 39.9, 116.4), GateVerdict.Allow, "master switch off: allowed");
Eq(Decide(true, true, f => f != "ceratopsidae", "ceratopsidae", "triceratops", 39.9, 116.4), GateVerdict.Allow, "family switch off: allowed");
Eq(Decide(true, true, allOn, "ceratopsidae", "nosuchgenus", 39.9, 116.4), GateVerdict.Allow, "unknown variant: fail open");
Eq(Decide(true, true, allOn, "macronaria", "argentinosaurus", 39.9, 116.4), GateVerdict.Allow, "non-flagship family: allowed");

// ---------- 2b. 1.1.0 lopgapfill genera ----------
Console.WriteLine("== lopgapfill genera (1.1.0) ==");
var gapfill = new (string Fam, string Genus, string Region, double InLat, double InLon, double OutLat, double OutLon)[]
{
    ("allosauridae", "cryolophosaurus", "Antarctica", -80, 0, -25, 135),
    ("allosauridae", "australovenator", "Australia", -25, 135, -80, 0),
    ("allosauridae", "maip", "South America", -34.6, -58.4, 41.25, -95.93),
    ("iguanodontia", "muttaburrasaurus", "Australia", -25, 135, 39.9, 116.4),
    ("iguanodontia", "leaellynasaura", "Australia", -38, 145, 39.9, 116.4),
    ("iguanodontia", "trinisaura", "Antarctica", -65, -57, -25, 135),
    ("ankylosauria", "minmi", "Australia", -26, 148, 41.25, -95.93),
    ("plateosauridae", "glacialisaurus", "Antarctica", -85, 160, 41.25, -95.93),
    ("dromaeosauridae", "imperobator", "Antarctica", -64, -57, 39.9, 116.4),
    ("macronaria", "savannasaurus", "Australia", -22, 143, 41.25, -95.93),
    ("macronaria", "isisaurus", "India", 20, 78, 39.9, 116.4),
    ("macronaria", "paralititan", "North Africa", 27, 30, -25, 135),
    ("diplodocoidea", "amargasaurus", "South America", -38, -69, 39.9, 116.4),
    ("abelisauridae", "masiakasaurus", "Madagascar", -17, 46, -34.6, -58.4),
    ("oviraptorosauria", "gigantoraptor", "Central Asia", 45, 100, -25, 135),
};
Eq(gapfill.Length, 15, "gapfill genus count");
foreach (var g in gapfill)
{
    Check(FlagshipTable.Homes[(g.Fam, g.Genus)].SequenceEqual(new[] { g.Region }), $"{g.Genus}: home is {g.Region}");
    Eq(Decide(true, true, allOn, g.Fam, g.Genus, g.InLat, g.InLon), GateVerdict.Allow, $"{g.Genus} allowed in {g.Region}");
    Eq(Decide(true, true, allOn, g.Fam, g.Genus, g.OutLat, g.OutLon), GateVerdict.Block, $"{g.Genus} vetoed outside {g.Region}");
    Eq(Decide(false, true, allOn, g.Fam, g.Genus, g.OutLat, g.OutLon), GateVerdict.Allow, $"{g.Genus}: standard world no-op");
    Eq(Decide(true, true, f => f != g.Fam, g.Fam, g.Genus, g.OutLat, g.OutLon), GateVerdict.Allow, $"{g.Genus}: family switch off allows");
    // adult / baby / nest / egg resolved code paths (runtime.db form family-type-age-...)
    foreach (var form in new[] { "adult-male", "adult-female", "baby-male", "baby-female", "nest-incubating", "nest-mature", "nest-empty", "egg-raw" })
    {
        string path = $"{g.Fam}-{g.Genus}-{form}";
        string? fam = FlagshipTable.FamilyOfCodePath(path);
        Eq(fam, g.Fam, $"family from path {path}");
        Eq(Decide(true, true, allOn, fam!, g.Genus, g.InLat, g.InLon), GateVerdict.Allow, $"{path} allowed in region");
        Eq(Decide(true, true, allOn, fam!, g.Genus, g.OutLat, g.OutLon), GateVerdict.Block, $"{path} vetoed outside region");
    }
}
// Boundaries of the new boxes
Check(FlagshipRegions.InRegion("Australia", -44, 112) && FlagshipRegions.InRegion("Australia", -10, 154), "Australia box corners inclusive");
Check(!FlagshipRegions.InRegion("Australia", -9.9, 135) && !FlagshipRegions.InRegion("Australia", -25, 154.1), "Australia box edges exclusive outside");
Check(FlagshipRegions.InRegion("Antarctica", -90, -180) && FlagshipRegions.InRegion("Antarctica", -60, 180), "Antarctica box corners inclusive");
Check(!FlagshipRegions.InRegion("Antarctica", -59.9, 0), "Antarctica box excludes -59.9");

// Fail-open: every OTHER variant of the new gated families stays allowed anywhere
foreach (var (fam, others) in new[]
{
    ("allosauridae", new[] { "allosaurus", "saurophaganax", "torvosaurus", "megalosaurus", "nosuchgenus" }),
    ("iguanodontia", new[] { "iguanodon", "mantellisaurus", "nosuchgenus" }),
    ("ankylosauria", new[] { "ankylosaurus", "tarchia", "euoplocephalus", "nosuchgenus" }),
    ("plateosauridae", new[] { "plateosaurus", "massospondylus", "nosuchgenus" }),
    ("dromaeosauridae", new[] { "utahraptor", "deinonychus", "nosuchgenus" }),
    ("macronaria", new[] { "argentinosaurus", "patagotitan", "nosuchgenus" }),
    ("diplodocoidea", new[] { "diplodocus", "apatosaurus", "nosuchgenus" }),
    ("oviraptorosauria", new[] { "oviraptor", "citipati", "nosuchgenus" }),
    ("abelisauridae", new[] { "nosuchgenus" }),
})
{
    Check(FlagshipTable.IsFlagshipFamily(fam), $"{fam} is a gated family");
    foreach (var o in others)
        foreach (var (la, lo) in new[] { (39.9, 116.4), (-80.0, 0.0), (-25.0, 135.0), (41.25, -95.93) })
            Eq(Decide(true, true, allOn, fam, o, la, lo), GateVerdict.Allow, $"{fam}:{o} unlisted variant fail-open at {la},{lo}");
    Eq(Decide(true, true, allOn, fam, null!, 39.9, 116.4), GateVerdict.Allow, $"{fam}: null variant allowed");
}
// Only the 15 gapfill genera were added to Homes beyond the original 65
Eq(FlagshipTable.Homes.Count(kv => kv.Key.Family != "abelisauridae" || kv.Key.Variant == "masiakasaurus")
   - FlagshipTable.Homes.Count(kv => new[] { "ceratopsidae", "tyrannosauridae", "spinosauridae", "carcharodontosauridae", "herrerasauridae" }.Contains(kv.Key.Family)),
   15, "non-original-family rows plus masiakasaurus == 15");
Eq(FlagshipTable.Homes.Count(kv => new[] { "ceratopsidae", "tyrannosauridae", "spinosauridae", "abelisauridae", "carcharodontosauridae", "herrerasauridae" }.Contains(kv.Key.Family)) - 1, 65, "original six families still hold exactly 65 rows (+masiakasaurus)");
// Code path derivation edge cases
Eq(FlagshipTable.FamilyOfCodePath("abelisauridae"), "abelisauridae", "bare family code");
Eq(FlagshipTable.FamilyOfCodePath("abelisauridae-carnotaurus-adult-male"), "abelisauridae", "original family resolved path");
Eq(FlagshipTable.FamilyOfCodePath("hitch"), null, "hitch not a flagship");
Eq(FlagshipTable.FamilyOfCodePath("lure-big-redmeat"), null, "lure not a flagship");
Eq(FlagshipTable.FamilyOfCodePath("allosauridaex-foo"), null, "prefix needs dash boundary");
Eq(FlagshipTable.FamilyOfCodePath(null!), null, "null path");

// ---------- 3. Flagship table completeness vs the installed packs ----------
Console.WriteLine("== flagship table vs installed packs ==");
string StripComments(string t)
{
    t = Regex.Replace(t, @"/\*.*?\*/", "", RegexOptions.Singleline);
    return string.Join("\n", t.Split('\n').Where(l => !l.TrimStart().StartsWith("//")));
}
var packFiles = new Dictionary<string, string>
{
    ["ceratopsidae"] = "lop-ceratops-1.2.1.zip",
    ["tyrannosauridae"] = "LoP-Tyranno-1.4.2-batch0.zip",
    ["spinosauridae"] = "LoP-Spino-1.1.0.zip",
    ["abelisauridae"] = "LoP-Abeli-1.0.11.zip",
    ["carcharodontosauridae"] = "LoP-Carchar-1.0.7.zip",
    ["herrerasauridae"] = "LoP-Herrerasauridae-1.0.0-v1.zip",
};
int extractedTotal = 0;
foreach (var (family, zipName) in packFiles)
{
    string zipPath = Path.Combine(modsDir, zipName);
    Check(File.Exists(zipPath), $"pack present: {zipName}");
    if (!File.Exists(zipPath)) continue;
    using var zip = ZipFile.OpenRead(zipPath);
    var entityEntries = zip.Entries.Where(e =>
        e.FullName.Contains("/entities/") && e.FullName.EndsWith(".json") &&
        !Regex.IsMatch(e.Name, "egg|nest|lure|hitch|carcass")).ToList();
    Eq(entityEntries.Count, 1, $"{family}: exactly one main entity file");
    using var reader = new StreamReader(entityEntries[0].Open());
    string json = StripComments(reader.ReadToEnd());
    using var doc = JsonDocument.Parse(json);
    var root = doc.RootElement;
    Eq(root.GetProperty("code").GetString(), family, $"{family}: entity code matches");
    var typeGroup = root.GetProperty("variantgroups").EnumerateArray()
        .First(g => g.GetProperty("code").GetString() == "type");
    var variants = typeGroup.GetProperty("states").EnumerateArray().Select(s => s.GetString()).ToList();
    extractedTotal += variants.Count;
    foreach (var v in variants)
        Check(FlagshipTable.TryGetHomes(family, v, out _), $"{family}:{v} has a home region in the table");
}
Eq(extractedTotal, 65, "extracted variant total");
Eq(FlagshipTable.Homes.Count, 80, "flagship table entry total (65 pack bijection + 15 lopgapfill)");

// ---------- 4. Flora tables from the real packs ----------
Console.WriteLine("== flora tables ==");
var assignments = new FloraAssignments();
var fixtureFiles = Directory.GetFiles(fixturesDir, "*.biomes.json").OrderBy(f => f).ToList();
Eq(fixtureFiles.Count, 8, "eight Floral Zones fixture tables");
foreach (var file in fixtureFiles)
{
    using var doc = JsonDocument.Parse(File.ReadAllText(file));
    var table = new PackFloraTable { Domain = Path.GetFileName(file).Replace(".biomes.json", "") };
    foreach (var section in new[] { "TreeBiomes", "BlockPatchBiomes" })
    {
        if (!doc.RootElement.TryGetProperty(section, out var obj)) continue;
        var target = section == "TreeBiomes" ? table.TreeBiomes : table.BlockPatchBiomes;
        foreach (var prop in obj.EnumerateObject())
            target[prop.Name] = prop.Value.EnumerateArray().Select(e => e.GetString()).ToList();
    }
    assignments.AddPack(table);
    Console.WriteLine($"INFO  {table.Domain}: {table.TreeBiomes.Count} tree, {table.BlockPatchBiomes.Count} patch species");
}
Eq(assignments.PackCount, 8, "assignments pack count");
Check(assignments.TreeSpeciesCount > 0, $"tree species loaded ({assignments.TreeSpeciesCount})");
Check(assignments.PatchSpeciesCount > 0, $"patch species loaded ({assignments.PatchSpeciesCount})");

// Cape tree: in-realm allowed, out-of-realm blocked, ocean blocked, vanilla ungated.
Check(assignments.TreeAllowed("floralzonescaperegion", "afrocarpusfalcatus", Realms.AtlanticAfrotropic), "cape afrocarpus allowed in atlantic afrotropic");
Check(assignments.TreeAllowed("floralzonescaperegion", "afrocarpusfalcatus", Realms.EasternAfrotropic), "cape afrocarpus allowed in eastern afrotropic");
Check(!assignments.TreeAllowed("floralzonescaperegion", "afrocarpusfalcatus", Realms.AtlanticNearctic), "cape afrocarpus blocked in atlantic nearctic");
Check(!assignments.TreeAllowed("floralzonescaperegion", "afrocarpusfalcatus", null), "cape afrocarpus blocked where no realm (ocean)");
Check(assignments.TreeAllowed("game", "oak", Realms.AtlanticNearctic), "vanilla oak is ungated");
Check(assignments.TreeAllowed("game", "oak", null), "vanilla oak allowed even with no realm");

// Patch decision driven by a real Cape patch species from the fixtures.
using (var doc = JsonDocument.Parse(File.ReadAllText(fixtureFiles.First(f => f.Contains("cape")))))
{
    var firstPatch = doc.RootElement.GetProperty("BlockPatchBiomes").EnumerateObject()
        .First(p => p.Value.GetArrayLength() > 0);
    string token = FloraAssignments.PatchPatternToken(firstPatch.Name);
    string homeRealm = firstPatch.Value.EnumerateArray().First().GetString();
    string awayRealm = Realms.All.First(r => r != homeRealm &&
        !firstPatch.Value.EnumerateArray().Any(e => e.GetString() == r));
    var codes = new[] { ("floralzonescaperegion", "flower-" + token + "-red") };
    Check(assignments.PatchAllowed(codes, homeRealm), $"cape patch '{token}' allowed in {homeRealm}");
    Check(!assignments.PatchAllowed(codes, awayRealm), $"cape patch '{token}' blocked in {awayRealm}");
    Check(assignments.PatchAllowed(new[] { ("game", "flower-daisy-red") }, awayRealm),
        "a code no table names (vanilla daisy) stays ungated");
    Console.WriteLine($"INFO  cape patch sample: token={token}, home={homeRealm}, away={awayRealm}");
}

// ---------- 5. Geographic cross-check for three packs ----------
Console.WriteLine("== cross-check: where can each pack's species appear? ==");
(string name, double lat, double lon)[] points =
{
    ("Cape Town", -33.9, 18.4), ("Alice Springs", -23.8, 133.9), ("Rome", 41.9, 12.5),
    ("Omaha", 41.25, -95.93), ("Beijing", 39.9, 116.4), ("Manaus", -3.1, -60.0), ("Auckland", -36.8, 174.8)
};
foreach (var file in fixtureFiles.Where(f => f.Contains("cape") || f.Contains("centralaustralian") || f.Contains("mediterranean")))
{
    string domain = Path.GetFileName(file).Replace(".biomes.json", "");
    using var doc = JsonDocument.Parse(File.ReadAllText(file));
    var speciesRealms = new List<List<string>>();
    foreach (var section in new[] { "TreeBiomes", "BlockPatchBiomes" })
    {
        if (!doc.RootElement.TryGetProperty(section, out var obj)) continue;
        foreach (var prop in obj.EnumerateObject())
            speciesRealms.Add(prop.Value.EnumerateArray().Select(e => e.GetString()).ToList());
    }
    foreach (var (pname, plat, plon) in points)
    {
        string realm = Realms.RealmAt(plat, plon);
        int allowedHere = speciesRealms.Count(r => r.Count == 0 || (realm != null && r.Contains(realm)));
        Console.WriteLine($"INFO  {domain} at {pname} ({realm}): {allowedHere}/{speciesRealms.Count} species allowed");
    }
    if (domain.Contains("cape"))
    {
        string omahaRealm = Realms.RealmAt(41.25, -95.93);
        Check(speciesRealms.All(r => !r.Contains(omahaRealm)), "cape pack: no species lists Omaha's realm");
        string capeRealm = Realms.RealmAt(-33.9, 18.4);
        Check(speciesRealms.Any(r => r.Contains(capeRealm)), "cape pack: at least one species allowed at Cape Town");
    }
    if (domain.Contains("centralaustralian"))
    {
        string aliceRealm = Realms.RealmAt(-23.8, 133.9);
        Check(speciesRealms.Any(r => r.Contains(aliceRealm)), "central australian pack: species allowed at Alice Springs");
    }
}

Console.WriteLine($"\n==== {passed} passed, {failures} failed ====");
return failures == 0 ? 0 : 1;
