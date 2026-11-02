import zipfile,glob,sys,re,pyjson5,json,fnmatch
M=r'%APPDATA%\VintagestoryData\Mods'
def load(k,f):
    zf=zipfile.ZipFile(glob.glob(M+rf'\FotSA-{k}-*.zip')[0])
    n=[x for x in zf.namelist() if x.endswith('/'+f+'-adult.json') and 'entities/' in x][0]
    t=zf.read(n).decode('utf-8-sig')
    try: return pyjson5.loads(t)
    except Exception: return json.loads(t)
def res(d,code):
    if not isinstance(d,dict): return d
    for k,v in d.items():
        if k.startswith('@'):
            if re.fullmatch(k[1:],code): return v
        elif fnmatch.fnmatch(code,k): return v
def find(n,key,out):
    if isinstance(n,dict):
        for k,v in n.items():
            if k==key: out.append(v)
            find(v,key,out)
    elif isinstance(n,list):
        for e in n: find(e,key,out)
for k,f,t,pre in [('Vombatidae','diprotodontidae','zygomaturustrilobus','diprotodontidae'),('Meiolaniidae','meiolaniidae','ninjemysoweni','meiolaniidae'),('Capreolinae','odocoileini','blastocerusdichotomus','odocoileini'),('Capreolinae','alceini','cervalcesscotti','alceini'),('Bovinae','bovinae','bubalusbrevicornis','bovinae'),('Bovinae','bovinae','bubalusmindorensis','bovinae'),('Pantherinae','pantherinae-panthera','atrox','pantherinae-panthera')]:
    d=load(k,f)
    code=f'{pre}-adult-male-{t}' if 'panthera' not in pre else f'{pre}-adult-male-atrox-normal'
    out=[]
    for key in ('hitBoxSizeByType','eyeHeightByType','sizeByType','weightByType'):
        o=[];find(d,key,o)
        print(t,key,[res(x,code) for x in o][:3])
