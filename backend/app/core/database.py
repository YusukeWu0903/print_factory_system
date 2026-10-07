# print_factory_system/backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
