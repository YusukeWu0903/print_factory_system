# print_factory_system/backend/app/schemas/__init__.py
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderStatusUpdate,
    WorkOrderResponse,
    WorkOrderListResponse,
)

__all__ = [
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "WorkOrderCreate",
    "WorkOrderUpdate",
    "WorkOrderStatusUpdate",
    "WorkOrderResponse",
    "WorkOrderListResponse",
]