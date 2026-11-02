import json,urllib.request,os,hashlib
aliases=["vsecomachina","floralzonescaperegion","floralzonescaribbeanregion","floralzonescentralaustralianregion","floralzonescircumborealregion","floralzonescosmopolitanregion","floralzoneseastasiaticregion","floralzonesmediterraneanregion","floralzonesneozeylandicregion"]
out=[]
for a in aliases:
    try:
        m=json.load(urllib.request.urlopen("https://mods.vintagestory.at/api/mod/"+a))["mod"]
    except Exception as e:
        print("FAIL",a,e); continue
    rs=m["releases"]
    if a=="vsecomachina":
        r=[x for x in rs if x["filename"]=="vsecomachina_0.6.1.zip"]
        r=r[0] if r else None
        print("EM latest:",rs[0]["filename"],rs[0]["tags"])
        if not r: print("0.6.1 not found"); continue
    else: r=rs[0]
    fn=r["filename"]; p=os.path.join("orig",fn)
    if not os.path.exists(p): urllib.request.urlretrieve(r["mainfile"],p)
    h=hashlib.sha256(open(p,'rb').read()).hexdigest()
    out.append(dict(alias=a,name=m["name"],modid=r["modidstr"],version=r["modversion"],file=fn,tags=r["tags"],created=r["created"],sha256=h,size=os.path.getsize(p)))
    print(a,r["modidstr"],r["modversion"],fn,r["tags"][-3:],r["created"],os.path.getsize(p))
json.dump(out,open("orig/releases.json","w"),indent=1)
