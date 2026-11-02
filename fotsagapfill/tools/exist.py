import zipfile,glob,re,os
M=r'%APPDATA%\VintagestoryData\Mods'
keys='aepyornis vorombe mullerornis cryptoprocta fossa diprotodon genyornis thylacoleo elasmotherium thambetochen chelychelynechen megatherium mylodon glossotherium doedicurus glyptodon macrauchenia toxodon hippopotamus lemerlei arctodus tremarctos camelops camelus lama vicugna procoptodon macropus equus hesperocyon palaeolagus ursus'.split()
for z in sorted(glob.glob(M+r'\FotSA-*.zip')):
    zf=zipfile.ZipFile(z)
    for n in zf.namelist():
        if n.endswith('.json') and 'lang' not in n:
            try:t=zf.read(n).decode('utf8','ignore').lower()
            except: continue
            hit=[k for k in keys if k in t]
            if hit and 'adult' in n: print(os.path.basename(z)[:22],n.split('/')[-1],hit)
