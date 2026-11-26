# print_factory_system/backend/app/schemas/work_order.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
from decimal import Decimal


from typing import Annotated, Literal
from pydantic import ConfigDict

ShortText = Annotated[str, Field(max_length=200)]
PieceName = Literal["student", "teacher", "answer"]


class PrintRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    colors: ShortText = ""
    presses: ShortText = ""
    demand: ShortText = ""
    waste: ShortText = ""
    reams: ShortText = ""
    note: ShortText = ""


class VersionPaper(BaseModel):
    quantity: ShortText = ""
    paper: ShortText = ""
    reams: ShortText = ""


class PrintPiece(BaseModel):
    instruction: ShortText = ""
    runs: list[PrintRun] = Field(default_factory=list, max_length=100)


class CombinedOrder(BaseModel):
    student_paper: VersionPaper
    teacher_paper: VersionPaper
    student: PrintPiece
    teacher: PrintPiece
    answer: PrintPiece


class PaperSections(BaseModel):
    plate_number: ShortText | None = None
    book_count: ShortText | None = None
    combined: CombinedOrder | None = None
    paper_size: Optional[str] = Field(default=None, max_length=200)
    paper_input: Optional[str] = Field(default=None, max_length=200)
    plate_info: Optional[str] = Field(default=None, max_length=200)
    press_size: Optional[str] = Field(default=None, max_length=200)
    press_actual: Optional[str] = Field(default=None, max_length=200)
    press_waste: Optional[str] = Field(default=None, max_length=200)
    press_runs: Optional[str] = Field(default=None, max_length=200)
    press_ink: Optional[str] = Field(default=None, max_length=200)
    finisher: Optional[str] = Field(default=None, max_length=200)
    due_date: Optional[str] = Field(default=None, max_length=200)


class WorkOrderBase(PaperSections):
    date: date
    client_id: int
    item_name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=1, ge=1)
    client_order_no: Optional[str] = None  # 客戶單號/製通單號 (可選)
    
    # 印刷廠紙本專屬欄位
    paper_weight: Optional[str] = None     # 紙磅 (例如 "150g", "100lb")
    paper_type: Optional[str] = None       # 紙別 (例如 "雙銅", "道林")
    cut_type: Optional[str] = None         # 裁別 (例如 "菊全開", "四開", "八開")
    front_side: Optional[int] = Field(default=None, ge=0)  # 正面色數
    back_side: Optional[int] = Field(default=None, ge=0)   # 反面色數
    operator: Optional[int] = Field(default=None, ge=0)    # 人員數
    notes: Optional[str] = None            # 備註 (其他特殊要求/後加工)

    # 費用結構
    paper_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    plate_fee: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    wage: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)

    @field_validator("item_name")
    @classmethod
    def strip_item_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("品名不可空白")
        return value


class WorkOrderCreate(WorkOrderBase):
    status: Literal["排印", "印製中"] = "印製中"
    remember_paper_size: bool = False


class WorkOrderUpdate(PaperSections):
    remember_paper_size: bool = False
    expected_revision: int = Field(ge=1)
    date: Optional[date] = None
    client_id: Optional[int] = None
    item_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    quantity: Optional[int] = Field(default=None, ge=1)
    paper_weight: Optional[str] = None
    paper_type: Optional[str] = None
    cut_type: Optional[str] = None
    client_order_no: Optional[str] = None
    front_side: Optional[int] = Field(default=None, ge=0)
    back_side: Optional[int] = Field(default=None, ge=0)
    operator: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None
    paper_fee: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    plate_fee: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    wage: Optional[Decimal] = Field(default=None, ge=0, max_digits=10, decimal_places=2)

    @field_validator("date", "client_id", "quantity", "paper_fee", "plate_fee", "wage")
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("此欄位不可為空")
        return value

    @field_validator("item_name")
    @classmethod
    def strip_item_name(cls, value: Optional[str]) -> str:
        if value is None or not value.strip():
            raise ValueError("品名不可空白")
        return value.strip()


class WorkOrderStatusUpdate(BaseModel):
    status: str


class WorkOrderResponse(WorkOrderBase):
    piece_reports: dict[PieceName, int] | None = None
    completed_quantity: Optional[int] = None
    revision: int
    updated_at: Optional[str] = None
    id: int
    total_amount: float
    status: str
    client_name: Optional[str] = None

    @classmethod
    def from_orm_with_client(cls, obj):
        data = {
            "id": obj.id, "piece_reports": obj.piece_reports,
            **{key: getattr(obj, key) for key in PaperSections.model_fields},
            "completed_quantity": obj.completed_quantity, "revision": obj.revision, "updated_at": obj.updated_at,
            "date": obj.date,
            "client_id": obj.client_id,
            "item_name": obj.item_name,
            "quantity": obj.quantity,
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


class WorkOrderListResponse(PaperSections):
    piece_reports: dict[PieceName, int] | None = None
    completed_quantity: Optional[int] = None
    revision: int
    updated_at: Optional[str] = None
    id: int
    date: date
    client_name: str
    client_id: int
    item_name: str
    quantity: int
    client_order_no: Optional[str] = None
    paper_weight: Optional[str] = None
    paper_type: Optional[str] = None
    cut_type: Optional[str] = None
    front_side: Optional[int] = None
    back_side: Optional[int] = None
    operator: Optional[int] = None
    notes: Optional[str] = None
    total_amount: float
    status: str
