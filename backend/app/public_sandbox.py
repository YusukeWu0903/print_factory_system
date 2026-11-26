"""Public trial entry point. Serve the built UI and business routes against a dedicated SQLite file."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

from app.api import clients, work_orders, reconciliation
from app.core.database import BACKEND_DIR, database_url, get_db
from app.core.schema import ensure_schema

trial_path = BACKEND_DIR / "public_sandbox.db"
if trial_path.is_symlink() or (trial_path.exists() and trial_path.stat().st_nlink > 1):
    raise RuntimeError("Public sandbox requires an independent file")
if database_url.database and trial_path.resolve() == Path(database_url.database).resolve():
    raise RuntimeError("Production and public sandbox must be separate")

trial_engine = create_engine(f"sqlite:///{trial_path.as_posix()}", connect_args={"check_same_thread": False})
ensure_schema(trial_engine)
TrialSession = sessionmaker(bind=trial_engine)
dist = BACKEND_DIR.parent / "frontend" / "dist"
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

def trial_db(request: Request):
    if request.headers.get("X-Data-Mode") != "sandbox":
        raise HTTPException(403, "此入口僅供測試")
    with TrialSession(info={"actor": "沙盒訪客"}) as db:
        yield db

from app.api.photo_ocr import router as photo_router
app.include_router(photo_router, prefix="/api/photos")
app.dependency_overrides[get_db] = trial_db
for prefix, router in [("clients", clients.router), ("work-orders", work_orders.router), ("reconciliation", reconciliation.router)]:
    app.include_router(router, prefix=f"/api/{prefix}")

from sqlalchemy.orm.exc import StaleDataError
from fastapi.responses import JSONResponse


@app.exception_handler(StaleDataError)
async def concurrent_update(request, exc):
    return JSONResponse(status_code=409, content={"detail": "工單已被其他人更新，請重新開啟比對。"})


@app.middleware("http")
async def trial_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Data-Mode"] = "sandbox"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.get("/api/auth/me")
def trial_access():
    return {"authenticated": True, "public_sandbox": True}

app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

@app.get("/")
@app.get("/create")
@app.get("/progress")
@app.get("/clients")
@app.get("/reconciliation")
def index():
    return FileResponse(dist / "index.html")
