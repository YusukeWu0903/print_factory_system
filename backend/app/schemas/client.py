# print_factory_system/backend/app/schemas/client.py
from pydantic import BaseModel
from typing import Optional


class ClientBase(BaseModel):
    name: str
    tax_id: Optional[str] = None
    billing_cycle: int = 1


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    tax_id: Optional[str] = None
    billing_cycle: Optional[int] = None


class ClientResponse(ClientBase):
    id: int

    @classmethod
    def from_orm_without_orders(cls, obj):
        data = {
            "id": obj.id,
            "name": obj.name,
            "tax_id": obj.tax_id,
            "billing_cycle": obj.billing_cycle,
        }
        return cls(**data)