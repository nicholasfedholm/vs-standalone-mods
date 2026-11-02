# Minimal JSON5-ish loader for VS asset files (comments, trailing commas, unquoted keys, single quotes not needed here)
import json,re
def _strip(t):
    out=[];i=0;n=len(t);ins=False
    while i<n:
        c=t[i]
        if ins:
            out.append(c)
            if c==chr(92): out.append(t[i+1]); i+=2; continue
            if c=='"': ins=False
            i+=1; continue
        if c=='"': ins=True; out.append(c); i+=1; continue
        if t.startswith('//',i):
            j=t.find('\n',i); i=n if j<0 else j; continue
        if t.startswith('/*',i):
            j=t.find('*/',i); i=n if j<0 else j+2; continue
        out.append(c); i+=1
    return ''.join(out)
def loads(t):
    t=_strip(t.lstrip('\ufeff'))
    t=re.sub(r',(\s*[}\]])',r'\1',t)
    t=re.sub(r'([{,]\s*)([A-Za-z_$][\w$]*)\s*:',r'\1"\2":',t)
    return json.loads(t,strict=False)
def load(p): return loads(open(p,encoding='utf-8-sig').read())
