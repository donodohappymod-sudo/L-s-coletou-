import hashlib, os
from datetime import timedelta
from database import init_db, get_session, Source, Content, utcnow
from collector import scan_source
from m3u_engine import deduplicate, fingerprint

init_db()
now=utcnow();
with get_session() as db:
    sources=db.query(Source).filter(Source.active==True).all()
    for src in sources:
        if src.next_check and src.next_check > now: continue
        try:
            result=scan_source(src.url, int(os.getenv('COLLECTOR_MAX_PAGES','30')), int(os.getenv('COLLECTOR_TIMEOUT','12')))
            items=deduplicate(result['items']); fp=fingerprint(items)
            src.status='ONLINE' if result['playlist_urls'] else 'ERRO'
            src.last_checked=now; src.next_check=now+timedelta(minutes=max(5,src.interval_minutes)); src.content_count=len(items); src.last_fingerprint=fp
            existing={(c.url.lower(),c.title.lower()):c for c in src.contents}
            added=0
            for it in items:
                key=(it.url.lower(),it.title.lower())
                c=existing.get(key)
                if c: c.category=it.category; c.group_name=it.group; c.logo=it.logo; c.attributes_json=str(it.attributes or {})
                else:
                    db.add(Content(title=it.title,url=it.url,category=it.category,group_name=it.group,logo=it.logo,attributes_json=str(it.attributes or {}),source_id=src.id)); added += 1
            src.new_contents=added
            db.commit()
        except Exception as e:
            src.status='ERRO'; src.last_checked=now; src.next_check=now+timedelta(minutes=max(5,src.interval_minutes)); db.commit()
