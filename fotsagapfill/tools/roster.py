import zipfile,glob,re,json,os
M=r'%APPDATA%\VintagestoryData\Mods'
out=open('work/roster.txt','w')
for z in sorted(glob.glob(M+r'\FotSA-*.zip')):
    zf=zipfile.ZipFile(z); n=os.path.basename(z)
    names=zf.namelist()
    ad=[x for x in names if re.search(r'entities/.*-adult\.json$',x)]
    out.write(f'## {n} adults={len(ad)}\n')
    for a in ad:
        t=zf.read(a).decode('utf8','ignore')
        m=re.search(r'"variantgroups"\s*:\s*\[(.*?)\]\s*,?\s*\n?\s*"',t,re.S)
        vg=re.findall(r'"code"\s*:\s*"(\w+)"[^}]*?"(?:states|loadFromProperties)"\s*:\s*(\[[^\]]*\]|"[^"]*")',t,re.S)
        out.write(f'{a.split("/")[-1]} :: {vg[:3]}\n')
    others=[x for x in names if x.endswith('.json') and 'entities' not in x and 'lang' not in x and 'config' in x.lower()]
    out.write(' config: '+','.join(others)+'\n')
