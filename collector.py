from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

UA="LosCollector/1.0"

def allowed(url):
    p=urlparse(url)
    if p.scheme not in ("http","https"): return False
    try:
        rp=RobotFileParser(f"{p.scheme}://{p.netloc}/robots.txt"); rp.read()
        return rp.can_fetch(UA,url)
    except Exception: return True

def crawl_site_for_playlists(start_url,max_pages=50,timeout=12):
    host=urlparse(start_url).netloc
    queue=[start_url]; seen=set(); playlists=[]; contents={}; warnings=[]
    s=requests.Session(); s.headers["User-Agent"]=UA
    while queue and len(seen)<max_pages:
        u=queue.pop(0)
        if u in seen or urlparse(u).netloc!=host or not allowed(u): continue
        seen.add(u)
        try:
            r=s.get(u,timeout=timeout); r.raise_for_status()
        except Exception as e:
            warnings.append(str(e)); continue
        ct=r.headers.get("content-type","").lower()
        text=r.text if ("text" in ct or "m3u" in ct or u.lower().split("?")[0].endswith((".m3u",".m3u8"))) else ""
        if "#EXTM3U" in text[:5000]:
            playlists.append(u); contents[u]=text
        if "html" not in ct: continue
        soup=BeautifulSoup(r.text,"html.parser")
        for a in soup.find_all("a",href=True):
            t=urljoin(u,a["href"]).split("#")[0]
            if urlparse(t).netloc!=host or t in seen: continue
            if t.lower().split("?")[0].endswith((".m3u",".m3u8")):
                if allowed(t):
                    try:
                        q=s.get(t,timeout=timeout)
                        if q.ok and "#EXTM3U" in q.text[:5000]:
                            if t not in playlists: playlists.append(t); contents[t]=q.text
                    except Exception as e: warnings.append(str(e))
            elif len(queue)<max_pages*3: queue.append(t)
    return {"playlists":list(dict.fromkeys(playlists)),"contents":contents,"warnings":warnings}
