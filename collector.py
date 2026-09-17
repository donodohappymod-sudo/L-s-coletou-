import re
import ipaddress
import socket
from collections import deque
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from m3u_engine import parse_m3u

UA='LosCollector/1.0 (+public-authorized-content)'
M3U_RE=re.compile(r'https?://[^\s"\'<>]+?\.(?:m3u8?|m3u)(?:\?[^\s"\'<>]*)?', re.I)

def valid_http(url):
    try:
        p=urlparse(url)
        if p.scheme not in ('http','https') or not p.hostname: return False
        host=p.hostname.lower()
        if host in ('localhost','localhost.localdomain'): return False
        try:
            ips={ipaddress.ip_address(host)}
        except ValueError:
            try: ips={ipaddress.ip_address(x[4][0]) for x in socket.getaddrinfo(host,None,type=socket.SOCK_STREAM)}
            except OSError: return False
        return all(not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved) for ip in ips)
    except Exception: return False

def fetch(url, timeout=12):
    if not valid_http(url): raise ValueError('Destino não permitido.')
    return requests.get(url, timeout=(4,timeout), headers={'User-Agent':UA}, allow_redirects=True, verify=True)

def looks_m3u(text, content_type=''):
    head=text[:5000].lstrip('\ufeff\r\n ')
    return head.upper().startswith('#EXTM3U') or '#EXTINF:' in head.upper() or 'mpegurl' in content_type.lower()

def scan_source(start_url, max_pages=30, timeout=12, progress=None):
    if not valid_http(start_url): raise ValueError('URL inválida. Use http:// ou https://.')
    root=urlparse(start_url); root_domain=root.netloc.lower(); q=deque([start_url]); seen=set(); playlist_urls=[]; raw_playlists={}; pages=0
    while q and pages < max_pages:
        url=q.popleft()
        if url in seen: continue
        seen.add(url); pages += 1
        if progress: progress(pages,max_pages,url,len(playlist_urls))
        try: r=fetch(url,timeout); final=r.url
        except requests.RequestException: continue
        ctype=r.headers.get('content-type','')
        body=r.text[:3_000_000]
        if looks_m3u(body,ctype) or final.lower().split('?')[0].endswith(('.m3u','.m3u8')):
            if final not in playlist_urls:
                playlist_urls.append(final); raw_playlists[final]=body
            continue
        for match in M3U_RE.findall(body):
            link=urljoin(final,match)
            if link not in playlist_urls: playlist_urls.append(link)
        soup=BeautifulSoup(body,'html.parser')
        for tag in soup.find_all(['a','link','source']):
            href=tag.get('href') or tag.get('src')
            if not href: continue
            link=urljoin(final,href)
            p=urlparse(link)
            if p.scheme not in ('http','https') or p.netloc.lower()!=root_domain: continue
            low=link.lower()
            if any(x in low for x in ('.m3u','.m3u8')):
                if link not in playlist_urls: playlist_urls.append(link)
            elif any(x in low for x in ('/playlist','/stream','/live','/tv','/iptv','/channel','/api/')) and link not in seen:
                q.append(link)
    for purl in list(playlist_urls):
        if purl in raw_playlists: continue
        try:
            r=fetch(purl,timeout); txt=r.text
            if looks_m3u(txt,r.headers.get('content-type','')): raw_playlists[purl]=txt
        except requests.RequestException: pass
    items=[]
    for purl,text in raw_playlists.items(): items.extend(parse_m3u(text,purl))
    return {'pages_scanned':pages,'playlist_urls':playlist_urls,'items':items}
