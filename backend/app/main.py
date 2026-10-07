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

@app.middleware("http")
async def disable_api_caching(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
        if hasattr(request.state, "data_mode"):
            response.headers["X-Data-Mode"] = request.state.data_mode
    return response

# Include routers
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
