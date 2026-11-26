# print_factory_system/backend/app/models/work_order.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, event, inspect
from sqlalchemy.orm import object_session


class WorkOrderStatus(str, enum.Enum):
    PLANNED = "排印"
    PRINTING = "印製中"
    COMPLETED_PENDING_BILLING = "已完成_待請款"
    BILLED = "已請款"


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plate_number = Column(String(200))
    book_count = Column(String(200))
    paper_size = Column(String(200), nullable=True)
    paper_input = Column(String(200), nullable=True)
    plate_info = Column(String(200), nullable=True)
    press_size = Column(String(200), nullable=True)
    press_actual = Column(String(200), nullable=True)
    press_waste = Column(String(200), nullable=True)
    press_runs = Column(String(200), nullable=True)
    press_ink = Column(String(200), nullable=True)
    finisher = Column(String(200), nullable=True)
    due_date = Column(String(200), nullable=True)
    combined = Column(JSON, nullable=True)
    piece_reports = Column(JSON, nullable=True)
    completed_quantity = Column(Integer, nullable=True)
    revision = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision}
    audit_key = Column(String(32))
    updated_at = Column(String(40))
    date = Column(Date, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    item_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    client_order_no = Column(String(100), nullable=True)  # 客戶單號/製通單號 (可選)
    
    # 印刷廠紙本專屬欄位
    paper_weight = Column(String(50), nullable=True)     # 紙磅 (例如 "150g", "100lb")
    paper_type = Column(String(100), nullable=True)      # 紙別 (例如 "雙銅", "道林")
    cut_type = Column(String(50), nullable=True)         # 裁別 (例如 "菊全開", "四開", "八開")
    front_side = Column(Integer, nullable=True)          # 正面 (數字，例如 4, 1, 0)
    back_side = Column(Integer, nullable=True)           # 反面 (數字，例如 1, 0)
    operator = Column(Integer, nullable=True)            # 人員數 (人數，數字)
    notes = Column(Text, nullable=True)                  # 備註 (其他特殊要求/後加工)

    # 費用結構
    paper_fee = Column(Numeric(10, 2), nullable=False, default=0)
    plate_fee = Column(Numeric(10, 2), nullable=False, default=0)
    wage = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    status = Column(
        SQLEnum(WorkOrderStatus),
        nullable=False,
        default=WorkOrderStatus.PRINTING,
        index=True
    )

    # Relationship
    client = relationship("Client", back_populates="work_orders")

    def __repr__(self):
        return f"<WorkOrder(id={self.id}, date='{self.date}', client_id={self.client_id}, item='{self.item_name}', total={self.total_amount}, status='{self.status}')>"

class OrderHistory(Base):
    __tablename__ = "order_history"
    id = Column(Integer, primary_key=True)
    audit_key = Column(String(32), nullable=False, index=True)
    order_id = Column(Integer, nullable=False)
    timestamp = Column(String(40), nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    changes = Column(JSON, nullable=False)


def printable(value):
    return value.value if isinstance(value, enum.Enum) else None if value is None else str(value)


def record(connection, order, action, changes):
    connection.execute(OrderHistory.__table__.insert().values(
        audit_key=order.audit_key or uuid4().hex, order_id=order.id,
        timestamp=order.updated_at if action != "刪除" else datetime.now(timezone.utc).isoformat(),
        actor=object_session(order).info.get("actor", "管理員"), action=action, changes=changes))


@event.listens_for(WorkOrder, "before_insert")
def stamp_creation(mapper, connection, order):
    order.audit_key = uuid4().hex
    order.updated_at = datetime.now(timezone.utc).isoformat()


@event.listens_for(WorkOrder, "after_insert")
def record_creation(mapper, connection, order):
    record(connection, order, "建立", {})


@event.listens_for(WorkOrder, "before_update")
def record_update(mapper, connection, order):
    changes = {}
    for column in mapper.columns:
        key = column.key
        if key in {"id", "revision", "updated_at", "audit_key"}:
            continue
        history = inspect(order).attrs[key].history
        if history.has_changes():
            before = history.deleted[0] if history.deleted else None
            if key == "piece_reports":
                for piece, amount in (order.piece_reports or {}).items():
                    previous = (before or {}).get(piece)
                    if previous != amount:
                        changes[piece + "_quantity"] = [printable(previous), printable(amount)]
                continue
            changes[key] = [printable(before), printable(getattr(order, key))]
    if changes:
        order.audit_key = order.audit_key or uuid4().hex
        order.updated_at = datetime.now(timezone.utc).isoformat()
        record(connection, order, "修改", changes)


@event.listens_for(WorkOrder, "after_delete")
def record_deletion(mapper, connection, order):
    record(connection, order, "刪除", {key: [printable(getattr(order,key)), None]
           for key in ("item_name","quantity","client_id","total_amount")})
