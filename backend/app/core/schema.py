"""Small, reversible migrations for the existing SQLite installation."""

from datetime import datetime
from pathlib import Path
import sqlite3

from sqlalchemy import inspect

from app.core.database import Base


def _backup_sqlite(database_path: Path) -> Path:
    backup_dir = database_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{database_path.stem}_{stamp}.db"
    suffix = 1
    while backup_path.exists():
        backup_path = backup_dir / f"{database_path.stem}_{stamp}_{suffix}.db"
        suffix += 1
    with sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True) as source:
        with sqlite3.connect(backup_path) as backup:
            source.backup(backup)
    return backup_path


def ensure_schema(engine) -> None:
    """Create new tables and add the one column missing from older databases."""

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    needs_order_number = "work_orders" in tables and "client_order_no" not in {
        column["name"] for column in inspector.get_columns("work_orders")
    }
    needs_session_table = bool(tables) and "auth_sessions" not in tables
    needs_session_credential = "auth_sessions" in tables and "credential_hash" not in {
        column["name"] for column in inspector.get_columns("auth_sessions")
    }

    if (needs_order_number or needs_session_table or needs_session_credential) and engine.url.get_backend_name() == "sqlite":
        database_name = engine.url.database
        if database_name and database_name != ":memory:":
            database_path = Path(database_name)
            if database_path.is_file():
                _backup_sqlite(database_path)

    if needs_order_number:
        if engine.url.get_backend_name() != "sqlite":
            raise RuntimeError("Existing non-SQLite databases require a manual migration")
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE work_orders ADD COLUMN client_order_no VARCHAR(100)"
            )

    if needs_session_credential:
        if engine.url.get_backend_name() != "sqlite":
            raise RuntimeError("Existing non-SQLite databases require a manual migration")
        with engine.begin() as connection:
            # Existing sessions are invalid until their holders log in again.
            connection.exec_driver_sql(
                "ALTER TABLE auth_sessions ADD COLUMN credential_hash VARCHAR(64) NOT NULL DEFAULT ''"
            )

    Base.metadata.create_all(bind=engine)
