# print_factory_system/backend/app/schemas/client.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    tax_id: Optional[str] = Field(default=None, pattern=r"^[0-9]{8}$")
    billing_cycle: int = Field(default=1, ge=1, le=31)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("客戶名稱不可空白")
        return value


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    tax_id: Optional[str] = Field(default=None, pattern=r"^[0-9]{8}$")
    billing_cycle: Optional[int] = Field(default=None, ge=1, le=31)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: Optional[str]) -> str:
        if value is None or not value.strip():
            raise ValueError("客戶名稱不可空白")
        return value.strip()

    @field_validator("billing_cycle")
    @classmethod
    def require_billing_cycle(cls, value: Optional[int]) -> int:
        if value is None:
            raise ValueError("結帳日不可為空")
        return value


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
