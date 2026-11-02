import json,sys,glob,zipfile
z=zipfile.ZipFile('staging/fotsagapfill-0.1.0.zip'); new=sys.argv[1]
P=json.loads(z.read('assets/fotsagapfill/patches/gapfill.json'))
def find(n,new,out):
    if isinstance(n,dict):
        for k,v in n.items():
            if new in k and isinstance(v,dict) and 'climate' in v: out.append((k,{a:v['climate'][a] for a in ('minTemp','maxTemp','minRain','maxRain') if a in v['climate']}))
            find(v,new,out)
    elif isinstance(n,list):
        for e in n: find(e,new,out)
o=[]
for p in P: find(p['value'],new,o)
print('climate',o[:2]); 
for n in z.namelist():
    if n.endswith('lang/en.json'):
        l=json.loads(z.read(n)); ks=[(k,v) for k,v in l.items() if new in k]
        if ks: print(n.split('/')[1],len(ks),ks[:4])
bio=[p for p in P if 'biomes' in json.dumps(p.get('dependsOn')) and new in json.dumps(p['value'])]; print('biorealm patches',len(bio),[p['value'] for p in bio][:1])
