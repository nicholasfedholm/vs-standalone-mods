"""Install merged zips into Mods (explicitly authorised), verify, restore from backup on failure."""
import os, shutil, hashlib, json, zipfile, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = r'%APPDATA%\VintagestoryData\Mods'
MG = os.path.join(ROOT, 'work', 'merged'); BK = os.path.join(ROOT, 'backup_mods')
man = json.load(open(os.path.join(ROOT, 'work', 'install_manifest.json')))
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
procs = subprocess.run(['powershell', '-Command', 'Get-Process | Where-Object {$_.Name -match "^(Vintagestory|VintagestoryServer|vsbench)"} | Select -Expand Name'], capture_output=True, text=True).stdout.strip()
assert not procs, procs
# Mods unchanged since step 1?
for n, (sz, mt) in man['before_listing'].items():
    st = os.stat(os.path.join(M, n)); assert (st.st_size, st.st_mtime) == (sz, mt), n
packs = list(man['touched'])
done = []
try:
    for n in packs:
        assert sha(os.path.join(MG, n)) != man['touched'][n]['sha256']
        shutil.copy2(os.path.join(MG, n), os.path.join(M, n)); done.append(n)
    shutil.copy2(os.path.join(MG, 'fotsagapfill-0.2.0.zip'), os.path.join(M, 'fotsagapfill-0.2.0.zip')); done.append('fotsagapfill-0.2.0.zip')
    res = {}
    for n in done:
        p = os.path.join(M, n)
        assert sha(p) == sha(os.path.join(MG, n)), 'hash mismatch ' + n
        assert zipfile.ZipFile(p).testzip() is None, 'testzip ' + n
        res[n] = {'sha256': sha(p), 'files': len(zipfile.ZipFile(p).namelist())}
except Exception as e:
    print('INSTALL FAILED', e, '- restoring')
    for n in done:
        if n in packs: shutil.copy2(os.path.join(BK, n), os.path.join(M, n))
    if os.path.exists(os.path.join(M, 'fotsagapfill-0.2.0.zip')): os.remove(os.path.join(M, 'fotsagapfill-0.2.0.zip'))
    sys.exit(1)
# rest of folder unchanged
changed = []; 
now = {e.name: (e.stat().st_size, e.stat().st_mtime) for e in os.scandir(M)}
for n, v in man['before_listing'].items():
    if n in done: continue
    if n not in now: changed.append(('missing', n))
    elif list(now[n]) != v: changed.append(('modified', n))
extra = [n for n in now if n not in man['before_listing'] and n not in done]
man['installed'] = res; man['other_changes'] = changed; man['extra_files'] = extra
json.dump(man, open(os.path.join(ROOT, 'work', 'install_manifest.json'), 'w'), indent=1)
for n, r in res.items(): print('INSTALLED', n, r['files'], 'files', r['sha256'][:16])
print('other mods changed:', changed, 'extra files:', extra, 'others checked:', len(man['before_listing']) - len(packs))
