# print_factory_system/backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import engine, Base
from app.models import Client, WorkOrder
from app.api import clients, work_orders, reconciliation

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="印刷廠工單與對帳系統",
    description="專為傳統代工印刷廠設計的輕量化工單與自動對帳系統",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(work_orders.router, prefix="/api/work-orders", tags=["Work Orders"])
app.include_router(reconciliation.router, prefix="/api/reconciliation", tags=["Reconciliation"])


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