import json,re,sys,zipfile,fnmatch,pyjson5,os
sys.path.insert(0,'.')
import specs
MODS=r'%APPDATA%\VintagestoryData\Mods'
sid=sys.argv[1]
S=[s for s in specs.SPECS if s['id']==sid][0]; t=S['new_type']
# apply built patch file: simple approach - read the built mod zip? use stage patches by overlaying 'replace' ops
zf=zipfile.ZipFile(os.path.join(MODS,S['donor_zip']))
patches=json.load(open('stage/assets/fotsagapfill/patches/gapfill.json',encoding='utf-8-sig'))
def match(k,code):
    if k.startswith('@'): return re.fullmatch(k[1:],code) is not None
    return fnmatch.fnmatchcase(code,k)
def setp(doc,path,val):
    parts=[p for p in path.split('/') if p]
    n=doc
    for p in parts[:-1]:
        n=n[int(p)] if isinstance(n,list) else n[p]
    last=parts[-1]
    if isinstance(n,list): n[int(last)]=val
    else: n[last]=val
for n in zf.namelist():
    if not (n.startswith('assets/') and '/entities/' in n and n.endswith('.json') and ('adult' in n or 'baby' in n)): continue
    doc=pyjson5.decode(zf.read(n).decode('utf-8-sig'))
    rel=n.split('/assets/')[0]
    fn=n.split('assets/')[1]
    dom,path=fn.split('/',1)
    for p in patches:
        if p.get('file')==f'{dom}:{path}':
            if p['op'] in('replace','add'):
                try: setp(doc,p['path'],p['value'])
                except Exception as e: pass
    age='adult' if 'adult' in n else 'baby'
    for sex in ('male',):
        code=f'{os.path.basename(n)[:-5].split("-")[0]}-{age}-{sex}-{t}'
        out=[]
        def chk(node,where):
            for k,v in node.items():
                if k.endswith('soundsByType') or k.endswith('soundByType') or k=='soundByType':
                    if isinstance(v,dict):
                        for kk,vv in v.items():
                            if match(kk,code): out.append((where+'/'+k,kk[:50],json.dumps(vv)[:110])); break
        def walk(o,path):
            if isinstance(o,dict):
                chk(o,path)
                for k,v in o.items(): walk(v,path+'/'+k)
            elif isinstance(o,list):
                for i,v in enumerate(o): walk(v,path+f'/{i}')
        walk(doc,'')
        print('##',os.path.basename(n),code)
        for o in out: print('  ',o[0][-48:],'|',o[1],'=>',o[2])
