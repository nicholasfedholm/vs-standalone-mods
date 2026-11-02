import zipfile,json,sys
z=zipfile.ZipFile('staging/fotsagapfill-0.1.0.zip'); P=json.loads(z.read('assets/fotsagapfill/patches/gapfill.json'))
new=sys.argv[1]; code=sys.argv[2]
def find(n,path,out):
    if isinstance(n,dict):
        if n.get('code')==code and 'enabledByType' in n and any(new in k for k in n['enabledByType']): out.append((path,list(n['enabledByType'].items())[:2]))
        for k,v in n.items(): find(v,path+'/'+k,out)
    elif isinstance(n,list):
        for i,e in enumerate(n): find(e,path+f'[{i}]',out)
for p in P:
    o=[];find(p['value'],p['path'],o)
    for x in o: print(x)
