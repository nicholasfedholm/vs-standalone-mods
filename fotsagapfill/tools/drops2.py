import json,sys,zipfile,os,pyjson5
sys.path.insert(0,'.')
import specs
MODS=r'%APPDATA%\VintagestoryData\Mods'
sid,rel=sys.argv[1],sys.argv[2]
S=[s for s in specs.SPECS if s['id']==sid][0]
zf=zipfile.ZipFile(os.path.join(MODS,S['donor_zip']))
n=[x for x in zf.namelist() if x.endswith(rel)][0]
d=pyjson5.decode(zf.read(n).decode('utf-8-sig'))
for bi,b in enumerate(d['server']['behaviors']):
    if 'drops' in b:
        for di,dr in enumerate(b['drops']):
            print(bi,di,dr.get('type'),dr.get('code') or json.dumps(dr.get('codeByType'))[:300])
