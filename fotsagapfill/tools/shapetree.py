import zipfile,sys,json
try:
    import pyjson5 as J
except: J=None
def load(t): return J.loads(t) if J else json.loads(t)
z,n=sys.argv[1],sys.argv[2]
zf=zipfile.ZipFile(z); s=load(zf.read(n).decode('utf8','ignore'))
print({k:s[k] for k in s if k not in('elements','animations')})
print('anims',[a.get('code') for a in s.get('animations',[])][:30])
def walk(e,d=0):
    f=[round(x,2) for x in e['from']];t=[round(x,2) for x in e['to']]
    print('  '*d+f"{e['name']} f{f} t{t} o{e.get('rotationOrigin')} r({e.get('rotationX',0)},{e.get('rotationY',0)},{e.get('rotationZ',0)}) uv{[ (k,v.get('uv')) for k,v in list(e.get('faces',{}).items())[:1]]}"[:200])
    for c in e.get('children',[]): walk(c,d+1)
for e in s['elements']: walk(e)
