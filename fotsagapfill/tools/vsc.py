"""usage: python -I work/vsc.py <id> : extract new+donor adult shape from stage zip/donor, run VsShapeCheck, print summary + static y/x/z extents"""
import zipfile,sys,subprocess,os,csv,glob,json
sys.path.insert(0,'work'); import specs
R=r'%USERPROFILE%\vs_scratch'; M=r'%APPDATA%\VintagestoryData\Mods'
s=[x for x in specs.SPECS if x['id']==sys.argv[1]][0]
z=zipfile.ZipFile('staging/fotsagapfill-0.1.0.zip')
new=[n for n in z.namelist() if s['new_type'] in n and '/shapes/entity/' in n and n.endswith(('adult.json', s['new_type']+'.json'))][0]
os.makedirs('work/x',exist_ok=True)
open(f'work/x/{s["id"]}-adult.json','wb').write(z.read(new))
dz=zipfile.ZipFile(os.path.join(M,s['donor_zip']))
dn=new.replace(s['new_type'],s['donor_type']).replace('fotsagapfill','x')
dn=[n for n in dz.namelist() if n.endswith(new.split('assets/')[1].split('/',1)[1].replace(s['new_type'],s['donor_type']))][0]
open(f'work/x/donor-{s["id"]}.json','wb').write(dz.read(dn))
def run(p,tag):
    r=subprocess.run(['dotnet',R+r'\shape-harness\bin\Release\net10.0\VsShapeCheck.dll',p,'--frames','4','--out',R+r'\fotsa-gapfill\work\x\out','--tag',tag],capture_output=True,text=True)
    return r
r=run(os.path.abspath(f'work/x/{s["id"]}-adult.json'),s['id'])
print('exit',r.returncode); print('\n'.join(r.stdout.strip().splitlines()[-12:]))
run(os.path.abspath(f'work/x/donor-{s["id"]}.json'),'donor-'+s['id'])
for tag in ('donor-'+s['id'],s['id']):
    rows=list(csv.DictReader(open(f'work/x/out/{tag}_static.csv')))
    k=[c for c in rows[0] if c.startswith('min') or c.startswith('max')]
    mn=[min(float(r[c]) for r in rows) for c in k if c.startswith('min')]; mx=[max(float(r[c]) for r in rows) for c in k if c.startswith('max')]
    print(tag,'bbox min',[round(v,2) for v in mn],'max',[round(v,2) for v in mx])
