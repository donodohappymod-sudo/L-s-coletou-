import hashlib, re
from dataclasses import dataclass, asdict
from urllib.parse import urlparse

@dataclass
class M3UItem:
    title: str
    url: str
    group: str = ''
    category: str = 'OUTRO'
    logo: str = ''
    attributes: dict|None = None
    source_url: str = ''

EXTINF_RE = re.compile(r'^#EXTINF:(?P<duration>-?\d+(?:\.\d+)?)\s*(?P<attrs>.*?),(?P<title>.*)$', re.I)
ATTR_RE = re.compile(r'([\w-]+)=(?:"([^"]*)"|([^\s]+))')

def parse_attrs(text):
    return {m.group(1).lower(): (m.group(2) if m.group(2) is not None else m.group(3)) for m in ATTR_RE.finditer(text or '')}

def classify(title, group=''):
    s=f'{title} {group}'.lower()
    if any(x in s for x in ('series','série','season','temporada','episódio','episode')): return 'SÉRIES'
    if any(x in s for x in ('filme','movie','cinema','film')): return 'FILMES'
    if any(x in s for x in ('live','tv','canal','news','sport','esporte','24h')): return 'CANAIS'
    return 'OUTRO'

def normalize_url(url):
    return url.strip().replace('\\','')

def parse_m3u(text, source_url=''):
    lines=[x.strip().lstrip('\ufeff') for x in text.replace('\r','').split('\n') if x.strip()]
    items=[]; pending=None
    for line in lines:
        if line.upper().startswith('#EXTINF:'):
            m=EXTINF_RE.match(line)
            if not m: pending=None; continue
            attrs=parse_attrs(m.group('attrs'))
            group=attrs.get('group-title','') or attrs.get('group','')
            logo=attrs.get('tvg-logo','')
            title=m.group('title').strip() or attrs.get('tvg-name','') or 'Sem título'
            pending=(title,group,logo,attrs)
        elif line.startswith('#'):
            continue
        else:
            url=normalize_url(line)
            if not (url.startswith(('http://','https://'))): pending=None; continue
            if pending:
                title,group,logo,attrs=pending
                items.append(M3UItem(title,url,group,classify(title,group),logo,attrs,source_url))
            pending=None
    return items

def deduplicate(items):
    out=[]; seen_url=set(); seen_key=set()
    for item in items:
        u=normalize_url(item.url).rstrip('/').lower()
        key=hashlib.sha1(f'{item.title.strip().lower()}|{item.group.strip().lower()}|{u}'.encode()).hexdigest()
        if u in seen_url or key in seen_key: continue
        seen_url.add(u); seen_key.add(key); out.append(item)
    return out

def export_m3u(items):
    lines=['#EXTM3U']
    for x in deduplicate(items):
        attrs=x.attributes or {}
        extra=[]
        if x.logo: extra.append(f'tvg-logo="{x.logo}"')
        if x.group: extra.append(f'group-title="{x.group}"')
        for k,v in attrs.items():
            if k not in ('tvg-logo','group-title','group','tvg-name') and v:
                extra.append(f'{k}="{v}"')
        attr_text=(' '+ ' '.join(extra)) if extra else ''
        lines.append(f'#EXTINF:-1{attr_text},{x.title}')
        lines.append(x.url)
    return '\n'.join(lines)+'\n'

def fingerprint(items):
    return hashlib.sha256('\n'.join(sorted(i.url for i in deduplicate(items))).encode()).hexdigest()
