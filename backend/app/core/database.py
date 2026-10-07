# print_factory_system/backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from os.path import normcase
from threading import Lock

from fastapi import HTTPException, Request

from app.core.config import BACKEND_DIR, get_settings

settings = get_settings()


def resolve_database_url(raw_url: str):
    database_url = make_url(raw_url)
    if database_url.get_backend_name() == "sqlite" and database_url.database not in (None, ":memory:"):
        database_path = Path(database_url.database)
        if not database_path.is_absolute():
            database_path = (BACKEND_DIR / database_path).resolve()
        database_url = database_url.set(database=str(database_path))
    return database_url


database_url = resolve_database_url(settings.DATABASE_URL)

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if database_url.get_backend_name() == "sqlite" else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
_sandbox_lock = Lock()
_sandbox_session_factory = None


def get_sandbox_session_factory():
    global _sandbox_session_factory
    if _sandbox_session_factory is None:
        with _sandbox_lock:
            if _sandbox_session_factory is None:
                sandbox_url = resolve_database_url(settings.SANDBOX_DATABASE_URL)
                if (
                    sandbox_url == database_url
                    or database_url.get_backend_name() == "sqlite"
                    and normcase(str(sandbox_url.database)) == normcase(str(database_url.database))
                ):
                    raise RuntimeError("測試與正式資料庫不可使用同一個位置")
                if sandbox_url.get_backend_name() != "sqlite" or sandbox_url.database in (None, ":memory:"):
                    raise RuntimeError("測試環境需要獨立的 SQLite 檔案")
                sandbox_engine = create_engine(
                    sandbox_url, connect_args={"check_same_thread": False}, echo=settings.DEBUG
                )
                from app.core.schema import ensure_schema
                ensure_schema(sandbox_engine)
                _sandbox_session_factory = sessionmaker(
                    autocommit=False, autoflush=False, bind=sandbox_engine
                )
    return _sandbox_session_factory


def get_auth_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db(request: Request):
    mode = request.headers.get("X-Data-Mode")
    if mode not in {"production", "sandbox"}:
        raise HTTPException(status_code=400, detail="資料環境無效")
    request.state.data_mode = mode
    db = (get_sandbox_session_factory() if mode == "sandbox" else SessionLocal)()
    try:
        yield db
    finally:
        db.close()
