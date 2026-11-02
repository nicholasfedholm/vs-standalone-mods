# Applies our JSON patches (RFC6902 subset VS uses: add/replace) to the real target assets and checks results.
import glob, json, os, re, sys, copy
sys.path.insert(0, os.path.dirname(__file__)); import j5
PACKS = {}
for pk in glob.glob("x/Floral*"):
    mi = {k.lower(): v for k, v in j5.load(pk + "/modinfo.json").items()}
    PACKS[mi["modid"].lower()] = pk
def target_path(loc, deps):
    dom, path = loc.split(":", 1)
    pack = PACKS[[d["modid"] for d in deps if d["modid"].startswith("floralzones")][0]]
    return os.path.normpath(os.path.join(pack, "assets", dom, *path.split("/")))
def unesc(s): return s.replace("~1", "/").replace("~0", "~")
def apply(doc, op):
    parts = [unesc(p) for p in op["path"].split("/")[1:]]
    cur = doc
    for p in parts[:-1]:
        if p not in cur: raise KeyError("missing parent " + p)
        cur = cur[p]
    last = parts[-1]
    if op["op"] == "replace":
        if last not in cur: raise KeyError("replace target missing " + op["path"])
        old = cur[last]; cur[last] = op["value"]; return old
    if op["op"] == "add":
        if last in cur: raise KeyError("add would overwrite " + op["path"])
        cur[last] = op["value"]; return None
    raise ValueError(op["op"])
def bylookup(d, code):
    for k, v in d.items():
        if re.match("^" + re.escape(k).replace(r"\*", ".*") + "$", code): return v
    return None
ok = True; docs = {}
for f in sorted(glob.glob("patch/assets/*/patches/*.json")):
    ops = json.load(open(f, encoding="utf-8"))           # strict JSON
    for i, op in enumerate(ops):
        assert {d["modid"] for d in op["dependsOn"]} >= {"vsecomachina"}, f
        tp = target_path(op["file"], op["dependsOn"])
        if tp not in docs: docs[tp] = j5.load(tp); docs[tp + "#orig"] = copy.deepcopy(docs[tp])
        try:
            old = apply(docs[tp], op)
            print("OK  %-48s #%d %-7s %-45s %s -> %s" % (os.path.basename(f), i, op["op"], op["file"].split("/")[-1] + op["path"], json.dumps(old)[:60], json.dumps(op["value"])[:60]))
        except Exception as e:
            ok = False; print("ERR", f, i, e)
# semantic checks on Cape leaves after patch
for bt in ("normal", "branchy"):
    tp = os.path.normpath(os.path.join(PACKS["floralzonescaperegion"], "assets/floralzonescaperegion/blocktypes/plant/leaves/%s.json" % bt))
    d, o = docs[tp], docs[tp + "#orig"]
    code = d["code"]
    for wood in ("afrocarpusfalcatus", "ocoteabullata", "searsialancea"):
        for ty in ("grown", "placed", "placed3"):
            c = "%s-%s-%s" % (code, ty, wood)
            beh = [b["name"] for b in bylookup(d["behaviorsByType"], c)]
            dec = bylookup(d["attributes"]["canDecayByType"], c)
            obeh = [b["name"] for b in bylookup(o["behaviorsByType"], c)]
            odec = bylookup(o["attributes"]["canDecayByType"], c)
            print("  %-40s before beh=%s decay=%s | after beh=%s decay=%s" % (c, obeh, odec, beh, dec))
            if ty == "grown" and not (dec is True and "PushEventOnBlockBroken" in beh): ok = False
            if ty != "grown" and (beh != obeh or dec != odec): ok = False
    # everything except behaviorsByType / canDecayByType must be unchanged
    d2 = copy.deepcopy(d); o2 = copy.deepcopy(o)
    for x in (d2, o2): x.pop("behaviorsByType"); x["attributes"].pop("canDecayByType")
    if d2 != o2: ok = False; print("unexpected diff in", tp)
# treegen: only the two leaves keys changed
for tp in [k for k in docs if k.endswith(".json") and "treegen" in k]:
    a, b = docs[tp], docs[tp + "#orig"]
    diff = [k for k in set(a["treeBlocks"]) | set(b["treeBlocks"]) if a["treeBlocks"].get(k) != b["treeBlocks"].get(k)]
    a2 = dict(a); b2 = dict(b); a2.pop("treeBlocks"); b2.pop("treeBlocks")
    if sorted(diff) != ["leavesBlockCode", "leavesBranchyBlockCode"] or a2 != b2: ok = False; print("bad treegen diff", tp, diff)
print("RESULT:", "PASS" if ok else "FAIL")
