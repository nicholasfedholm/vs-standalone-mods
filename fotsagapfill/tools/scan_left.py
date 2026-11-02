import json,re,sys
sys.path.insert(0,'.')
import specs
d=json.load(open('stage/assets/fotsagapfill/patches/gapfill.json',encoding='utf-8-sig'))
sid=sys.argv[1]
S=[s for s in specs.SPECS if s['id']==sid][0]; t=S['new_type']
seen=set()
def walk(o,path,inkey,rel):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,path+[k],inkey or (isinstance(k,str) and t in k and not (k.startswith('@') and False)),rel)
    elif isinstance(o,list):
        for i,v in enumerate(o): walk(v,path+[i],inkey,rel)
    elif isinstance(o,str) and inkey and t not in o and re.search(r'creature/|entity/|item/|shapes/|sound',o):
        key=(rel,str(path[-1])[:60],o)
        if key not in seen:
            seen.add(key); print(rel[-24:],'|',str(path[-1])[:70],'=>',o[:110])
for p in d:
    if t in json.dumps(p): walk(p,[],False,p.get('file',''))
