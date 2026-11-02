import zipfile,glob,pyjson5,sys,re
M=r'%APPDATA%\VintagestoryData\Mods'
k,sub=sys.argv[1],sys.argv[2]
zf=zipfile.ZipFile(glob.glob(M+rf'\FotSA-{k}-*.zip')[0])
n=[x for x in zf.namelist() if x.endswith(sub)][0]
s=pyjson5.loads(zf.read(n).decode('utf-8-sig'))
print('==',n.split('shapes/')[-1],'tex',s.get('textureWidth'),s.get('textureHeight'),'anims',sorted({a['code'] for a in s.get('animations',[])}))
def w(e,d):
    f=[round(x,1) for x in e['from']];t=[round(x,1) for x in e['to']]
    print('  '*d+e['name'],f,[round(b-a,1) for a,b in zip(f,t)],'rot',[e.get('rotationX',0),e.get('rotationY',0),e.get('rotationZ',0)] if any(e.get(r) for r in('rotationX','rotationY','rotationZ')) else '')
    for c in e.get('children',[]): w(c,d+1)
for e in s['elements']: w(e,0)
