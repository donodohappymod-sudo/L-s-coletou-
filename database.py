import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from sqlalchemy import create_engine, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

BASE = Path(os.getenv('DATA_DIR','data'))
BASE.mkdir(parents=True, exist_ok=True)
db_url = os.getenv('DATABASE_URL','').strip()
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://','postgresql://',1)
if not db_url:
    db_url = f"sqlite:///{BASE / 'loscollector.db'}"

engine = create_engine(db_url, future=True, pool_pre_ping=True, connect_args={'check_same_thread': False} if db_url.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Source(Base):
    __tablename__='sources'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text, unique=True)
    status: Mapped[str] = mapped_column(String(30), default='NÃO VERIFICADO')
    last_checked: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=1440)
    content_count: Mapped[int] = mapped_column(Integer, default=0)
    last_fingerprint: Mapped[str|None] = mapped_column(String(64), nullable=True)
    new_contents: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    contents: Mapped[list['Content']] = relationship(back_populates='source', cascade='all, delete-orphan')

class Content(Base):
    __tablename__='contents'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30), default='OUTRO')
    group_name: Mapped[str|None] = mapped_column(String(255), nullable=True)
    logo: Mapped[str|None] = mapped_column(Text, nullable=True)
    attributes_json: Mapped[str|None] = mapped_column(Text, nullable=True)
    source_id: Mapped[int] = mapped_column(ForeignKey('sources.id', ondelete='CASCADE'), index=True)
    status: Mapped[str] = mapped_column(String(30), default='NÃO VERIFICADO')
    response_detail: Mapped[str|None] = mapped_column(String(500), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    source: Mapped[Source] = relationship(back_populates='contents')

class StudioProject(Base):
    __tablename__='studio_projects'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default='')
    genre: Mapped[str] = mapped_column(String(500), default='')
    cover: Mapped[str|None] = mapped_column(Text, nullable=True)
    logo: Mapped[str|None] = mapped_column(Text, nullable=True)
    platform: Mapped[str] = mapped_column(String(80), default='Instagram Reels')
    format: Mapped[str] = mapped_column(String(20), default='9:16')
    duration: Mapped[int] = mapped_column(Integer, default=15)
    file_path: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Setting(Base):
    __tablename__='settings'
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default='')

def init_db():
    Base.metadata.create_all(engine)

def get_session():
    return SessionLocal()

def seed_admin():
    from auth import hash_password
    email=os.getenv('ADMIN_EMAIL','').strip().lower()
    password=os.getenv('ADMIN_INITIAL_PASSWORD','')
    if not email or not password: return False
    with get_session() as db:
        user=db.query(User).filter_by(email=email).first()
        if not user:
            db.add(User(email=email,password_hash=hash_password(password)))
            db.commit()
            return True
    return False

def utcnow(): return datetime.now(timezone.utc)

def iso(dt): return dt.isoformat() if dt else ''
