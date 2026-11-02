import zipfile,json,re,os,sys,pyjson5
sys.path.insert(0,'work'); import specs
M=r'%APPDATA%\VintagestoryData\Mods'
Z='staging/fotsagapfill-0.2.0.zip'
want=sys.argv[1:]
sel=[s for s in specs.SPECS if (not want or s['id'] in want) and s['donor_zip']]
zf=zipfile.ZipFile(Z); print('zip test:', zf.testzip() or 'OK', len(zf.namelist()),'files')
bad=0
for n in zf.namelist():
    if n.endswith('.json'):
        try: pyjson5.loads(zf.read(n).decode('utf-8-sig'))
        except Exception as e:
            try: json.loads(zf.read(n).decode('utf-8-sig')); pass
            except Exception as e2: print('JSON FAIL',n,str(e2)[:120]); bad+=1
print('json parse failures:',bad)
patches=json.loads(zf.read('assets/fotsagapfill/patches/gapfill.json'))
donors={}
def donor(mod):
    for s in specs.SPECS:
        if s['donor_zip'].split('-v')[0].lower().endswith(mod) or mod in s['donor_zip'].lower():
            return zipfile.ZipFile(os.path.join(M,s['donor_zip']))
def unptr(p): return [x.replace('~1','/').replace('~0','~') for x in p.split('/')[1:]]
fail=0; docs={}
for p in patches:
    if p.get('dependsOn',[{}])[0].get('modid')=='biomes': 
        continue
    mod,rel=p['file'].split(':'); dz=donor(mod)
    n=f'assets/{mod}/{rel}'
    if n not in docs: docs[n]=(dz,pyjson5.loads(dz.read(n).decode('utf-8-sig')))
    node=docs[n][1]
    try:
        path=unptr(p['path'])
        for k in path[:-1]: node=node[int(k)] if isinstance(node,list) else node[k]
        last=path[-1]; last=int(last) if isinstance(node,list) else last
        node[last]  # must exist for replace
        node[last]=p['value']
    except Exception as e: print('PATCH PATH FAIL',p['file'],p['path']); fail+=1
print('patch path failures:',fail,'of',len(patches),'patches')
# reference check
names=set(zf.namelist())
for s in sel:
    new=s['new_type']; dz=donor(s['donor_zip'].split('-')[1].lower()); dom=[x for x in dz.namelist() if x.endswith('modinfo.json')]
    mod=json.loads(dz.read('modinfo.json'))['modid']; allnames=names|set(dz.namelist())
    refs=set()
    for n,(d,doc) in docs.items():
        if mod not in n: continue
        def w(x):
            if isinstance(x,dict):
                for k,v in x.items(): w(v)
            elif isinstance(x,list):
                for e in x: w(e)
            elif isinstance(x,str) and new in x and x.startswith('entity/'): refs.add(x)
        w(doc)
    miss=[]
    for r in sorted(refs):
        r2=r.replace('{type}',new)
        ok=any(f'assets/{mod}/{k}/{r2}{e}' in allnames for k in('shapes','textures') for e in('.json','.png'))
        if not ok: miss.append(r)
    print(s['id'],'entity refs',len(refs),'unresolved',miss)
    cl=[n for n in names if new in n]; print(s['id'],'cloned assets:',len(cl))
    # texture dims
    from PIL import Image; import io
    for n in cl:
        if n.endswith('.png'):
            a=Image.open(io.BytesIO(zf.read(n))).size
            o=None
            for cand in (n.replace(new,s['donor_type']),):
                if cand in dz.namelist(): o=Image.open(io.BytesIO(dz.read(cand))).size
            if o is None: o=a
            print(' texture',os.path.basename(n),a,'donor',o,'MATCH' if a==o else 'MISMATCH')

# ---- extra 0.2.0 checks ----
def loadj(t):
    try: return pyjson5.loads(t)
    except Exception: return json.loads(t)

import subprocess, tempfile, shutil, csv, hashlib
print('modinfo:', json.loads(zf.read('modinfo.json'))['version'], json.loads(zf.read('modinfo.json'))['modid'])
tmp = os.path.join(os.environ.get('TEMP','.'), 'v2_extract'); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
zf.extractall(tmp)
DLL = r'shape-harness\bin\Release\net10.0\VsShapeCheck.dll'
alldz = {}
for s in specs.SPECS:
    if s['donor_zip']: alldz[s['donor_zip']] = zipfile.ZipFile(os.path.join(M, s['donor_zip']))
tot_e = tot_w = nshape = 0; texbad = 0; texunres = []
for s in sel:
    new = s['new_type']
    for n in sorted(names):
        if new in n and '/shapes/entity/' in n and n.endswith('.json') and 'antlers' not in n:
            nshape += 1
            r = subprocess.run(['dotnet', DLL, os.path.join(tmp, n), '--out', os.path.join(tmp, '_o'), '--frames', '4'], capture_output=True, text=True)
            m = re.search(r'findings: (\d+) error, (\d+) warn', r.stdout)
            e, w = (int(m.group(1)), int(m.group(2))) if m else (-1, -1)
            tot_e += max(e, 0); tot_w += max(w, 0)
            if e != 0 or w != 0: print('  SHAPECHECK', n.split('/shapes/')[1], e, w)
    # texture references of every cloned shape (entity + item)
    for n in sorted(names):
        if new in n and '/shapes/' in n and n.endswith('.json'):
            sh = loadj(zf.read(n).decode('utf-8-sig'))
            codes = set((sh.get('textures') or {}).keys())
            used = set()
            def wf(el):
                for ch in el:
                    for f in (ch.get('faces') or {}).values():
                        t = f.get('texture')
                        if t and t.startswith('#'): used.add(t[1:])
                    wf(ch.get('children') or [])
            wf(sh.get('elements', []))
            miss = used - codes - {'skin', 'seat', 'antlers', 'antler'}
            if miss: texunres.append((n.split('/shapes/')[1], sorted(miss)))
            for c, tp in (sh.get('textures') or {}).items():
                if isinstance(tp, str) and ':' not in tp:
                    dom = n.split('/')[1]
                    if f'assets/{dom}/textures/{tp}.png' not in names and not any(f'assets/{dom}/textures/{tp}.png' in d.namelist() for d in alldz.values()):
                        texbad += 1; print('  TEXPATH MISSING', n.split('/shapes/')[1], c, tp)
print('shapes checked', nshape, 'errors', tot_e, 'warnings', tot_w)
print('shape face texture codes unresolved (excluding entity-provided skin):', texunres[:10], len(texunres))
print('texture paths missing:', texbad)
# every texture file in the zip: path exists and is a PNG that opens
from PIL import Image; import io
pngs = [n for n in names if n.endswith('.png')]
badpng = 0
for n in pngs:
    try: Image.open(io.BytesIO(zf.read(n))).verify()
    except Exception as ex: badpng += 1; print('BAD PNG', n)
print('pngs', len(pngs), 'bad', badpng)
print('0.1.0 md5', hashlib.md5(open('staging/fotsagapfill-0.1.0.zip','rb').read()).hexdigest(), 'expected', open('work/zip010.md5').read().split()[0])

# ---- arctodus (own domain, vanilla bear donor) ----
ent = pyjson5.loads(zf.read('assets/fotsagapfill/entities/animal/mammal/arctodus-adult.json').decode('utf-8-sig'))
txt = json.dumps(ent)
print('arctodus: code', ent.get('code'), '| lion/panther refs:', len(re.findall(r'lion|panther|pantherinae|cub', txt, re.I)),
      '| behaviors client/server:', [b['code'] for b in ent['client']['behaviors']][:6], [b['code'] for b in ent['server']['behaviors']][:8])
shp = ent['client'].get('shape', {}).get('base')
print('arctodus shape', shp, 'exists', any(n.endswith(shp + '.json') for n in names) if shp else None)
tex = ent['client'].get('textures', {})
for k, v in tex.items():
    bs = v.get('base') if isinstance(v, dict) else None
    alts = [a for a in (v.get('alternates') or [])] if isinstance(v, dict) else []
    for b in ([bs] if bs else []) + [a['base'] for a in alts]:
        dom = 'fotsagapfill' if ':' not in b else b.split(':')[0]
        print('  texture', k, b, 'in zip', f'assets/fotsagapfill/textures/{b}.png' in names if ':' not in b else 'game')
r = subprocess.run(['dotnet', DLL, os.path.join(tmp, 'assets/fotsagapfill/shapes/entity/animal/mammal/arctodus/simus-adult.json'), '--out', os.path.join(tmp, '_o'), '--frames', '8'], capture_output=True, text=True)
print('arctodus shapecheck:', re.search(r'findings: .*', r.stdout).group(0) if re.search(r'findings: .*', r.stdout) else r.stdout[-200:])
