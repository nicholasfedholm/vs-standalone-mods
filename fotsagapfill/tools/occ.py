import zipfile,glob,json,sys,re,pyjson5
M=r'%APPDATA%\VintagestoryData\Mods'
k,old=sys.argv[1],sys.argv[2]
zf=zipfile.ZipFile(glob.glob(M+rf'\FotSA-{k}-*.zip')[0])
for n in zf.namelist():
    if old in n: print('FILE',n.split(k.lower()+'/',1)[-1] if False else n[:120])
for n in zf.namelist():
    if n.endswith('.json') and n.startswith('assets/') and '/shapes/' not in n:
        t=zf.read(n).decode('utf-8-sig','ignore')
        if old in t and not n.endswith('en.json') : 
            c=t.count(old); print('REF',n[:110],c)
            if 'entities/' in n:
                for m in re.finditer(r'.{0,60}'+old+r'.{0,50}',t):
                    print('   ',m.group(0).replace('\n',' ').strip()[:140])
