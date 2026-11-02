# Static check: does Eco Machina 0.6.1 pick up each Floral Zones NEW-wood log tree?
# Mirrors the decompiled rules in vsecomachina.Core.TreeBlockClassifier, ModResinLogSubstitution and
# TaperedLogMesher.TryResolveLogTextureSet / ResolveConnectorTextureBlock. Run from the workspace root.
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import j5

VANILLA = r"%APPDATA%\Vintagestory\assets"
PACKS = sorted(glob.glob("x/Floral*"))
PATCHED = "--patched" in sys.argv          # apply our treegen leaf-code replacements before checking
PATCH_DIR = "patch/assets/ecomachinafloralzones/patches"

# ---------- Eco Machina classifier (TreeBlockClassifier) ----------
EXCL = ("fruittree-", "ferntree-", "bamboo-", "lognarrow-", "leavesnarrow-")
def em_classify(path):
    p = path.lower()
    if p.startswith(EXCL): return None, "excluded-family"
    if "-placed-" in p: return None, "placed-rejected"
    if "leavesbranchy" in p: return "BranchyLeaves", "ok"
    if p.startswith(("log-", "logsection-", "log_")) or p == "log": return "Wood", "ok"
    if p.startswith("leaves"): return "Leaves", "ok"
    return None, "not-tree"
def em_generated(path):
    p = path.lower()
    return "-grown-" in p or p.startswith(("log-grown-", "logsection-grown-"))
def em_resin_grown(domain, path):
    if domain == "game": return None
    for pre in ("log-resin-", "log-resinharvested-"):
        if path.startswith(pre): return "log-grown-" + path[len(pre):]
    return None

# ---------- asset helpers ----------
def tex_exists(loc, default_domain):
    dom, path = (loc.split(":", 1) if ":" in loc else (default_domain, loc))
    rel = os.path.join("textures", *path.split("/")) + ".png"
    for pk in PACKS:
        if os.path.exists(os.path.join(pk, "assets", dom, rel)): return True
    if dom == "game":
        for sub in ("game", "survival", "creative"):
            if os.path.exists(os.path.join(VANILLA, sub, rel)): return True
    return False

def wood_list(pack, domain):
    f = os.path.join(pack, "assets", domain, "worldproperties", "block", "wood.json")
    return [v["code"] if "code" in v else v["Code"] for v in j5.load(f)["variants"]] if os.path.exists(f) else []

def blocktype_states(bt, domain, pack):
    out = {}
    for g in bt.get("variantgroups", []):
        st = list(g.get("states", []))
        lfp = g.get("loadFromProperties")
        if lfp:
            d, p = lfp.split(":", 1) if ":" in lfp else (domain, lfp)
            f = os.path.join(pack, "assets", d, "worldproperties", *p.split("/")) + ".json"
            if os.path.exists(f):
                st += [v.get("code", v.get("Code")) for v in j5.load(f)["variants"]]
        out[g["code"]] = st
    return out

def bylookup(d, code):
    """VS *ByType resolution: first key whose wildcard matches the full code wins."""
    for k, v in d.items():
        rx = "^" + re.escape(k).replace(r"\*", ".*") + "$"
        if re.match(rx, code, re.I) or re.match(rx, code.split(":")[-1], re.I): return v
    return None

def load_blocktypes(pack, domain):
    bts = {}
    for f in glob.glob(os.path.join(pack, "assets", domain, "blocktypes", "**", "*.json"), recursive=True):
        try: bt = j5.load(f)
        except Exception: continue
        bts.setdefault(bt.get("code"), []).append((f, bt))
    return bts

def find_block(bts, domain, pack, path):
    """Return (file, blocktype, variant dict) that generates block path, else None."""
    code = path.split("-")[0]
    for f, bt in bts.get(code, []):
        st = blocktype_states(bt, domain, pack)
        keys = list(st.keys())
        parts = path.split("-")[1:]
        if len(parts) != len(keys): continue
        if all(parts[i] in st[k] for i, k in enumerate(keys)):
            return f, bt, dict(zip(keys, parts))
    return None

def resolve_textures(bt, fullcode, variant):
    tx = bt.get("textures") or bylookup(bt.get("texturesByType", {}), fullcode) or {}
    out = {}
    for k, v in tx.items():
        base = v.get("base") if isinstance(v, dict) else None
        if not base: continue
        for vk, vv in variant.items(): base = base.replace("{" + vk + "}", vv)
        out[k] = base
    return out

def em_texture_split(tex):
    """Mimic TryResolveLogTextureSet: need up/down/N/S/E/W (with 'all' fallback); bark=4-face group, end=2-face group."""
    faces = {}
    for f in ("up", "down", "north", "south", "east", "west"):
        faces[f] = tex.get(f, tex.get("all"))
    if any(v is None for v in faces.values()): return None, "legacy-path(missing face keys)"
    groups = {}
    for f, v in faces.items(): groups.setdefault(v, []).append(f)
    sizes = sorted(len(g) for g in groups.values())
    if sizes == [2, 4]:
        bark = [k for k, g in groups.items() if len(g) == 4][0]
        end = [k for k, g in groups.items() if len(g) == 2][0]
        return (bark, end), "grouped-4/2"
    return None, "axis/legacy-path(groups=%s)" % sizes

# ---------- treegen patches (our own, applied in --patched mode) ----------
def load_our_patches():
    rep = {}
    for f in glob.glob(os.path.join(PATCH_DIR, "*.json")):
        for op in json.load(open(f, encoding="utf-8")):
            rep.setdefault(op["file"].lower(), []).append(op)
    return rep

def main():
    ours = load_our_patches() if PATCHED else {}
    rows = []
    for pack in PACKS:
        if "vsecomachina" in pack: continue
        mi = {k.lower(): v for k, v in j5.load(os.path.join(pack, "modinfo.json")).items()}; domain = mi["modid"].lower()
        bts = load_blocktypes(pack, domain)
        for tgf in sorted(glob.glob(os.path.join(pack, "assets", "game", "worldgen", "treegen", "*.json"))):
            tg = j5.load(tgf); tb = tg.get("treeBlocks", {})
            name = os.path.basename(tgf)[:-5]
            for op in ours.get(("game:worldgen/treegen/%s.json" % name).lower(), []):
                assert op["op"] == "replace" and op["path"].startswith("/treeBlocks/")
                key = op["path"].split("/")[-1]
                assert key in tb, (name, key)
                tb[key] = op["value"]
            log = tb.get("logBlockCode", "")
            if not log.startswith(domain + ":log-grown-"): continue      # NEW-wood log trees only
            wood = log.split(":")[1][len("log-grown-"):-3]
            r = dict(pack=pack.split("-v")[0][len("x/FloralZones"):].replace("Region", ""), domain=domain, treegen=name, wood=wood, problems=[])
            # 1. trunk log block
            codes = [("log", log)]
            if tb.get("otherLogBlockCode"): codes.append(("other", tb["otherLogBlockCode"]))
            if tb.get("trunkSegmentBase"):
                for sv in tb.get("trunkSegmentVariants", []): codes.append(("section", tb["trunkSegmentBase"] + sv + "-ud"))
            for role, c in codes:
                d, p = c.split(":", 1) if ":" in c else ("game", c)
                fb = find_block(bts, d, pack, p) if d == domain else ("vanilla", None, None)
                if fb is None: r["problems"].append("%s block not generated: %s" % (role, c)); continue
                cls, why = em_classify(p)
                if cls != "Wood": r["problems"].append("%s %s: EM %s" % (role, c, why)); continue
                if role == "log":
                    if not em_generated(p): r["problems"].append("log not 'generated' for auto-claim")
                    tex = resolve_textures(fb[1], c, fb[2])
                    split, how = em_texture_split(tex)
                    r["uv"] = how
                    if not split: r["problems"].append("log texture split: " + how)
                    else:
                        r["bark"], r["end"] = split
                        for t in split:
                            if not tex_exists(t, domain): r["problems"].append("texture missing: " + t)
                    for k, t in tex.items():
                        if k.startswith("inside") or k in ("all", "up", "down", "north", "south", "east", "west"):
                            if not tex_exists(t, domain): r.setdefault("warn", set()).add("missing tex %s=%s" % (k, t))
                    # -ns / -we variants exist (EM maps them back to -ud)
                    for ax in ("ns", "we"):
                        if not find_block(bts, d, pack, p[:-2] + ax): r["problems"].append("axis variant missing " + ax)
                elif role == "other":
                    g = em_resin_grown(d, p)
                    r["resin"] = "resin-context or ->" + (g or "NONE")
                    if g and not find_block(bts, d, pack, g): r["problems"].append("resin grown twin missing " + g)
                    rt = resolve_textures(fb[1], c, fb[2])
                    r["resinbark"] = all(k in rt for k in ("resinbark1", "resinbark2"))
                elif role == "section":
                    m = re.match(r"logsection-([^-]+)-(.+)-(ne|nw|se|sw)-(ud)$", p)
                    reg = "log-%s-%s-ud" % (m.group(1), m.group(2)) if m else None
                    if not reg or not find_block(bts, d, pack, reg): r["problems"].append("section->regular log map failed " + p)
                    r["section"] = "->" + (reg or "?")
            # 2. leaves
            for role in ("leavesBlockCode", "leavesBranchyBlockCode"):
                c = tb.get(role, "")
                d, p = c.split(":", 1) if ":" in c else ("game", c)
                if d == domain and not find_block(bts, d, pack, p): r["problems"].append("%s not generated: %s" % (role, c))
                cls, why = em_classify(p)
                r[role] = (p, cls or why)
                if cls is None: r["problems"].append("%s: EM %s (%s)" % (role, why, p))
            rows.append(r)
    species = sorted({(r["pack"], r["wood"]) for r in rows})
    for r in rows:
        r["warn"] = sorted(r.get("warn", []))
    json.dump(rows, open("tools/verify_%s.json" % ("patched" if PATCHED else "orig"), "w"), indent=1)
    for r in rows:
        print("%-16s %-26s %-30s %s | %s" % (r["pack"], r["wood"], r["treegen"], "OK" if not r["problems"] else "FAIL", "; ".join(r["problems"])))
    print("species:", len(species), "treegens:", len(rows), "with problems:", sum(1 for r in rows if r["problems"]))

main()
