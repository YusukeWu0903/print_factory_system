# print_factory_system/backend/app/models/__init__.py
from app.models.client import Client
from app.models.work_order import WorkOrder

__all__ = ["Client", "WorkOrder"]