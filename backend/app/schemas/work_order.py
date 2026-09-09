# print_factory_system/backend/app/schemas/work_order.py
from pydantic import BaseModel
from typing import Optional
from datetime import date


class WorkOrderBase(BaseModel):
    date: date
    client_id: int
    item_name: str
    quantity: int = 1
    client_order_no: Optional[str] = None  # 客戶單號/製通單號 (可選)
    
    # 印刷廠紙本專屬欄位
    paper_weight: Optional[str] = None     # 紙磅 (例如 "150g", "100lb")
    paper_type: Optional[str] = None       # 紙別 (例如 "雙銅", "道林")
    cut_type: Optional[str] = None         # 裁別 (例如 "菊全開", "四開", "八開")
    client_order_no: Optional[str] = None # 客戶單號/製通單號
    front_side: Optional[int] = None       # 正面色數 (數字，例如 4, 1, 0)
    back_side: Optional[int] = None        # 反面色數 (數字，例如 1, 0)
    operator: Optional[int] = None         # 人員數 (人數，數字)
    notes: Optional[str] = None            # 備註 (其他特殊要求/後加工)

    # 費用結構
    paper_fee: float = 0.0
    plate_fee: float = 0.0
    wage: float = 0.0


class WorkOrderCreate(WorkOrderBase):
    pass


class WorkOrderUpdate(BaseModel):
    date: Optional[date] = None
    client_id: Optional[int] = None
    item_name: Optional[str] = None
    quantity: Optional[int] = None
    client_order_no: Optional[str] = None
    paper_weight: Optional[str] = None
    paper_type: Optional[str] = None
    cut_type: Optional[str] = None
    client_order_no: Optional[str] = None
    front_side: Optional[int] = None
    back_side: Optional[int] = None
    operator: Optional[int] = None
    notes: Optional[str] = None
    paper_fee: Optional[float] = None
    plate_fee: Optional[float] = None
    wage: Optional[float] = None


class WorkOrderStatusUpdate(BaseModel):
    status: str


class WorkOrderResponse(WorkOrderBase):
    id: int
    total_amount: float
    status: str
    client_name: Optional[str] = None

    @classmethod
    def from_orm_with_client(cls, obj):
        data = {
            "id": obj.id,
            "date": obj.date,
            "client_id": obj.client_id,
            "item_name": obj.item_name,
            "quantity": obj.quantity,
            "client_order_no": obj.client_order_no,
            "paper_weight": obj.paper_weight,
            "paper_type": obj.paper_type,
            "cut_type": obj.cut_type,
            "client_order_no": obj.client_order_no,
            "front_side": obj.front_side,
            "back_side": obj.back_side,
            "operator": obj.operator,
            "notes": obj.notes,
            "paper_fee": float(obj.paper_fee),
            "plate_fee": float(obj.plate_fee),
            "wage": float(obj.wage),
            "total_amount": float(obj.total_amount),
            "status": obj.status.value if hasattr(obj.status, 'value') else str(obj.status),
            "client_name": obj.client.name if obj.client else None,
        }
        return cls(**data)


class WorkOrderListResponse(BaseModel):
    id: int
    date: date
    client_name: str
    client_id: int
    item_name: str
    quantity: int
    client_order_no: Optional[str] = None
    total_amount: float
    status: str