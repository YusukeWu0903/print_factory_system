# print_factory_system/backend/app/models/work_order.py
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class WorkOrderStatus(str, enum.Enum):
    PRINTING = "印製中"
    COMPLETED_PENDING_BILLING = "已完成_待請款"
    BILLED = "已請款"


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
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