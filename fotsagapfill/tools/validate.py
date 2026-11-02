import zipfile,json,re,os,sys,pyjson5
sys.path.insert(0,'work'); import specs
M=r'%APPDATA%\VintagestoryData\Mods'
Z='staging/fotsagapfill-0.1.0.zip'
want=sys.argv[1:]
sel=[s for s in specs.SPECS if not want or s['id'] in want]
zf=zipfile.ZipFile(Z); print('zip test:', zf.testzip() or 'OK', len(zf.namelist()),'files')
bad=0
for n in zf.namelist():
    if n.endswith('.json'):
        try: pyjson5.loads(zf.read(n).decode('utf-8-sig'))
        except Exception as e:
            try: json.loads(zf.read(n).decode('utf-8-sig')); print('note: pyjson5 nesting limit, strict json OK:',n.split('/')[-1])
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
            o=Image.open(io.BytesIO(dz.read(n.replace(new,s['donor_type'])))).size
            print(' texture',os.path.basename(n),a,'donor',o,'MATCH' if a==o else 'MISMATCH')
