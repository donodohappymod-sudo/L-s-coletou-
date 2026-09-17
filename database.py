import sqlite3
from pathlib import Path
DB=Path("data/loscollector.sqlite3")
DB.parent.mkdir(exist_ok=True)

def db(): return sqlite3.connect(DB)
def init_db():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS sources(url TEXT PRIMARY KEY,entries INTEGER,updated_at TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS snapshots(url TEXT PRIMARY KEY,m3u TEXT,updated_at TEXT)")
        c.commit()
def save_source(url,entries):
    with db() as c: c.execute("INSERT OR REPLACE INTO sources VALUES(?,?,datetime('now'))",(url,entries))
def list_sources():
    with db() as c:
        return [{"url":r[0],"entries":r[1],"updated_at":r[2]} for r in c.execute("SELECT * FROM sources ORDER BY updated_at DESC")]
def save_snapshot(url,m3u):
    with db() as c: c.execute("INSERT OR REPLACE INTO snapshots VALUES(?,?,datetime('now'))",(url,m3u))
def load_snapshot(url):
    with db() as c:
        r=c.execute("SELECT m3u FROM snapshots WHERE url=?",(url,)).fetchone()
        return r[0] if r else None
