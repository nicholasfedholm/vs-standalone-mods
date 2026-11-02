"""Build work/merged/fotsagapfill-0.2.0.zip containing only Arctodus (from staging addon)."""
import os, zipfile, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = zipfile.ZipFile(os.path.join(ROOT, 'staging', 'fotsagapfill-0.2.0.zip'))
out = os.path.join(ROOT, 'work', 'merged', 'fotsagapfill-0.2.0.zip')
if os.path.exists(out): os.remove(out)
mi = {"type": "content", "modid": "fotsagapfill", "name": "FotSA Gap-Fill: Giant Short-faced Bear",
      "authors": ["Nick (generated)"],
      "description": "Adds the giant short-faced bear (Arctodus simus) as a standalone hostile animal, built on the vanilla bear assets. Needs no other animal pack.",
      "version": "0.2.0", "side": "Universal"}
keep = [n for n in A.namelist() if n.startswith('assets/fotsagapfill/') and not n.endswith('/') and '/patches/' not in n]
with zipfile.ZipFile(out, 'w') as z:
    z.writestr('modinfo.json', json.dumps(mi, indent=2) + '\n', compress_type=zipfile.ZIP_DEFLATED)
    for n in keep:
        z.writestr(n, A.read(n), compress_type=zipfile.ZIP_DEFLATED)
print(len(keep) + 1, 'files', os.path.getsize(out))
