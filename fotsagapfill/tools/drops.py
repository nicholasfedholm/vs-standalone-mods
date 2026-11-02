import json,re,sys,zipfile,os,pyjson5
sys.path.insert(0,'.')
import specs
MODS=r'%APPDATA%\VintagestoryData\Mods'
sid=sys.argv[1]
S=[s for s in specs.SPECS if s['id']==sid][0]; t=S['new_type']
patches=json.load(open('stage/assets/fotsagapfill/patches/gapfill.json',encoding='utf-8-sig'))
for p in patches:
    if t in json.dumps(p['value']) and 'drops' in p['path'].lower():
        print(p['file'][-34:],p['path'])
        v=p['value']
        def f(o):
            if isinstance(o,dict):
                for k,x in o.items():
                    if t in k or 'code' in k or isinstance(x,(dict,list)): pass
                print('   ',json.dumps(o)[:600])
        f(v)
