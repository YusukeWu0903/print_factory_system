"""Factory runtime. Each release has a separate environment; business data lives outside it."""
import argparse
from datetime import datetime
from logging.handlers import RotatingFileHandler
import logging
from pathlib import Path
import os
import sqlite3
import sys
import uuid

release = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(release / "backend"))

def backup(source, destination):
    if not source.is_file():
        raise SystemExit("Database does not exist")
    destination.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]
    target = destination / f"ledger-{name}.db"
    temp = target.with_suffix(".partial")
    try:
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as src, sqlite3.connect(temp) as dst:
            src.backup(dst)
            if dst.execute("pragma integrity_check").fetchone() != ("ok",):
                raise RuntimeError("Backup failed integrity check")
        src.close()
        dst.close()
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    print(target)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["password", "serve", "backup"])
    parser.add_argument("home", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--port", type=int, default=18200)
    args = parser.parse_args()
    home = args.home.resolve()
    data = home / "data"
    data.mkdir(parents=True, exist_ok=True)
    db = data / "ledger.db"
    if args.command == "backup":
        return backup(db, args.destination or home / "backups")
    credential = home / "admin.env"
    if args.command == "password":
        from getpass import getpass
        from app.core.passwords import hash_password
        from app.core.set_admin_password import save_password_hash
        password = getpass("Factory administrator password (12+ characters): ")
        if len(password) < 12 or password != getpass("Repeat password: "):
            raise SystemExit("Password too short or mismatch")
        return save_password_hash(credential, hash_password(password))
    from dotenv import dotenv_values
    password_hash = dotenv_values(credential).get("ADMIN_PASSWORD_HASH")
    if not password_hash:
        raise SystemExit("Run password setup first.")
    os.environ.update(DATABASE_URL=f"sqlite:///{db.as_posix()}", SANDBOX_DATABASE_URL=f"sqlite:///{(data/'sandbox.db').as_posix()}", ADMIN_PASSWORD_HASH=password_hash, DEBUG="False")
    logs = home / "logs"
    logs.mkdir(exist_ok=True)
    handler = RotatingFileHandler(logs / "service.log", maxBytes=2_000_000, backupCount=4, encoding="utf8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    from app.main import app
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    version = (release / "VERSION").read_text().strip()
    logging.info("Starting release %s", version)
    @app.get("/api/version")
    def installed_version():
        return {"revision": version}
    dist = release / "frontend/dist"
    # The development API's root is a JSON greeting. Replace only that route.
    app.router.routes[:] = [r for r in app.router.routes if r.path != "/"]
    app.mount("/assets", StaticFiles(directory=dist/"assets"), name="assets")
    @app.get("/")
    @app.get("/progress")
    @app.get("/clients")
    @app.get("/create")
    @app.get("/reconciliation")
    def page():
        return FileResponse(dist/"index.html")
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_config=None, access_log=False)

if __name__ == "__main__":
    main()
