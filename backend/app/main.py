# print_factory_system/backend/app/main.py
from fastapi import Depends, FastAPI, Request
from app.core.config import get_settings
from app.core.database import engine
from app.core.schema import ensure_schema
from app.models import Client, WorkOrder, AuthSession
from app.api import auth, clients, work_orders, reconciliation
from app.api.auth import require_admin

settings = get_settings()

# Preserve a SQLite backup before upgrading an existing schema.
ensure_schema(engine)

app = FastAPI(
    title="印刷廠工單與對帳系統",
    description="專為傳統代工印刷廠設計的輕量化工單與自動對帳系統",
    version="1.0.0",
    debug=settings.DEBUG,
)

from sqlalchemy.orm.exc import StaleDataError
from fastapi.responses import JSONResponse


@app.exception_handler(StaleDataError)
async def concurrent_update(request, exc):
    return JSONResponse(status_code=409, content={"detail": "工單已被其他人更新，請重新開啟比對。"})


@app.middleware("http")
async def disable_api_caching(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        if hasattr(request.state, "data_mode"):
            response.headers["X-Data-Mode"] = request.state.data_mode
    return response

# Include routers
from app.api.photo_ocr import router as photo_router
from app.core.database import get_db
app.include_router(photo_router, prefix="/api/photos", dependencies=[Depends(require_admin), Depends(get_db)])
from app.api.staff import router as staff_router
app.include_router(staff_router, prefix="/api/staff")
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"], dependencies=[Depends(require_admin)])
app.include_router(work_orders.router, prefix="/api/work-orders", tags=["Work Orders"], dependencies=[Depends(require_admin)])
app.include_router(reconciliation.router, prefix="/api/reconciliation", tags=["Reconciliation"], dependencies=[Depends(require_admin)])


@app.get("/")
async def root():
    return {
        "message": "印刷廠工單與對帳系統 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
