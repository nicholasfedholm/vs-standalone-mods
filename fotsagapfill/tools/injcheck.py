import zipfile,json,sys
sys.path.insert(0,'work'); import specs
z=zipfile.ZipFile('staging/fotsagapfill-0.1.0.zip'); P=json.loads(z.read('assets/fotsagapfill/patches/gapfill.json'))
vals=[{p['path'].split('/')[-1]:p['value']} for p in P if 'biomes' not in json.dumps(p.get('dependsOn'))]
def find(n,field,new,out):
    if isinstance(n,dict):
        for k,v in n.items():
            if k==field and isinstance(v,dict):
                out.extend((kk,vv) for kk,vv in v.items() if new in kk)
            find(v,field,new,out)
    elif isinstance(n,list):
        for e in n: find(e,field,new,out)
want=sys.argv[1:]
for s in specs.SPECS:
    if want and s['id'] not in want: continue
    new=s['new_type']; bad=[]; seen={}
    for f in set(list(s.get('fields',{}))+list(s.get('inject',{}))):
        out=[]
        for v in vals: find(v,f,new,out)
        seen[f]=len(out)
        exp=s.get('inject',{}).get(f) or s.get('fields',{}).get(f)
        if not out: bad.append(f+':ABSENT'); continue
        # first occurrence value check
        if f in s.get('inject',{}):
            for k,v in exp.items():
                if (k,v) not in out: bad.append(f+':'+k)
        else:
            for g,v in exp.items():
                if not any(((g in k) or g=='*') and vv==v for k,vv in out): bad.append(f+':'+g)
    print(s['id'],'OK' if not bad else 'PROBLEM '+str(bad),seen if want else '')
