import re

def parse_m3u(text, source=""):
    lines=[x.strip() for x in text.replace("\r","").split("\n") if x.strip()]
    out=[]; cur=None
    for line in lines:
        if line.startswith("#EXTINF"):
            attrs=dict(re.findall(r'([\w-]+)="([^"]*)"',line))
            title=line.split(",",1)[1].strip() if "," in line else attrs.get("tvg-name","Sem título")
            cur={"name":attrs.get("tvg-name") or title,"logo":attrs.get("tvg-logo",""),
                 "group":attrs.get("group-title",""),"tvg_id":attrs.get("tvg-id",""),
                 "url":"","source":source}
        elif not line.startswith("#") and cur:
            cur["url"]=line; out.append(cur); cur=None
    return out

def key(e):
    return (e.get("url","").strip().lower(),e.get("name","").strip().lower())

def merge_entries(entries):
    seen=set(); out=[]
    for e in entries:
        if e.get("url") and key(e) not in seen:
            seen.add(key(e)); out.append(e)
    return out

def category(e):
    g=(e.get("group") or "").lower(); n=(e.get("name") or "").lower()
    if any(x in g for x in ["series","série","tv show"]) or re.search(r"\b(s\d{1,2}|season|temporada|episode|epis[oó]dio)\b",n):
        return "Séries"
    if any(x in g for x in ["movie","filme","cinema"]): return "Filmes"
    if any(x in g for x in ["live","canais","channel","tv"]): return "Canais ao vivo"
    return e.get("group") or "Outros"

def organize_entries(entries):
    for e in entries: e["category"]=category(e)
    return sorted(entries,key=lambda x:(x["category"],x["name"].lower()))

def esc(x): return str(x).replace('"',"&quot;")

def generate_m3u(entries):
    out=["#EXTM3U"]
    for e in entries:
        attrs=[]
        for k,tag in [("tvg_id","tvg-id"),("name","tvg-name"),("logo","tvg-logo"),("category","group-title")]:
            if e.get(k): attrs.append(f'{tag}="{esc(e[k])}"')
        out.append("#EXTINF:-1 "+ " ".join(attrs)+","+e.get("name","Sem título"))
        out.append(e["url"])
    return "\n".join(out)+"\n"
