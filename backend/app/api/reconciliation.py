# print_factory_system/backend/app/api/reconciliation.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
from calendar import monthrange
import re
from app.core.database import get_db
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.client import Client
from app.models.statement import Statement, IssuedOrder
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, ConfigDict
from typing import List as TypingList

router = APIRouter(prefix="", tags=["Reconciliation"])


# ===== Pydantic Schemas =====

class ReconciliationWorkOrder(BaseModel):
    id: int
    date: date
    item_name: str
    quantity: int
    total_amount: Decimal
    status: str
    paper_weight: Optional[str] = None
    paper_type: Optional[str] = None
    cut_type: Optional[str] = None
    front_side: Optional[int] = None
    back_side: Optional[int] = None
    operator: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReconciliationSummary(BaseModel):
    client_id: int
    client_name: str
    month: str  # "2026-08"
    period_start: date
    period_end: date
    total_amount: Decimal
    work_order_count: int
    work_orders: List[ReconciliationWorkOrder]


class ReconciliationConfirmRequest(BaseModel):
    month: str  # "2026-08"
    client_id: int
    work_order_ids: List[int]


class ReconciliationConfirmResponse(BaseModel):
    success: bool
    message: str
    statement_id: int
    updated_count: int
    total_amount: Decimal


# ===== Helper Functions =====

def parse_month(month_str: str) -> tuple:
    """解析 '2026-08' 格式，回傳 (year, month)"""
    try:
        if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month_str):
            raise ValueError
        year, month = map(int, month_str.split('-'))
        if year < 1:
            raise ValueError
        return year, month
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="月份格式錯誤，請使用 YYYY-MM 格式（如 2026-08）"
        )


def get_billing_period(year: int, month: int, billing_cycle: int) -> tuple[date, date]:
    """A named month ends on that client's cutoff day (or the month's last day)."""
    end_date = date(year, month, min(billing_cycle, monthrange(year, month)[1]))
    previous_year, previous_month = (year - 1, 12) if month == 1 else (year, month - 1)
    previous_cutoff = date(
        previous_year,
        previous_month,
        min(billing_cycle, monthrange(previous_year, previous_month)[1]),
    )
    return previous_cutoff + timedelta(days=1), end_date


def billing_month_for_date(order_date: date, billing_cycle: int) -> str:
    cutoff = min(billing_cycle, monthrange(order_date.year, order_date.month)[1])
    if order_date.day <= cutoff:
        return f"{order_date.year}-{order_date.month:02d}"
    year, month = (
        (order_date.year + 1, 1)
        if order_date.month == 12
        else (order_date.year, order_date.month + 1)
    )
    return f"{year}-{month:02d}"


# ===== API Endpoints =====

@router.get("/summary", response_model=ReconciliationSummary)
def get_reconciliation_summary(
    month: str = Query(..., description="月份 YYYY-MM 格式"),
    client_id: int = Query(..., gt=0, description="客戶 ID"),
    db: Session = Depends(get_db),
):
    """查詢指定月份、客戶的待請款工單彙總"""
    
    # 驗證客戶存在
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客戶不存在"
        )
    
    year, month_num = parse_month(month)
    start_date, end_date = get_billing_period(year, month_num, client.billing_cycle)
    
    # 查詢該月份、該客戶、狀態為「已完成_待請款」的工單
    query = db.query(WorkOrder).options(joinedload(WorkOrder.client)).filter(
        WorkOrder.client_id == client_id,
        WorkOrder.status == WorkOrderStatus.COMPLETED_PENDING_BILLING,
        WorkOrder.date >= start_date,
        WorkOrder.date <= end_date,
    ).order_by(WorkOrder.date.asc(), WorkOrder.id.asc())
    
    work_orders = query.all()
    
    # 計算總金額
    total_amount = sum(wo.total_amount for wo in work_orders)
    
    # 組裝回傳資料
    wo_list = [
        ReconciliationWorkOrder(
            id=wo.id,
            date=wo.date,
            item_name=wo.item_name,
            quantity=wo.quantity,
            total_amount=wo.total_amount,
            status=wo.status.value if hasattr(wo.status, 'value') else str(wo.status),
            paper_weight=wo.paper_weight,
            paper_type=wo.paper_type,
            cut_type=wo.cut_type,
            front_side=wo.front_side,
            back_side=wo.back_side,
            operator=wo.operator,
            notes=wo.notes,
        )
        for wo in work_orders
    ]
    
    return ReconciliationSummary(
        client_id=client.id,
        client_name=client.name,
        month=f"{year}-{month_num:02d}",
        period_start=start_date,
        period_end=end_date,
        total_amount=total_amount,
        work_order_count=len(work_orders),
        work_orders=wo_list,
    )


@router.post("/confirm", response_model=ReconciliationConfirmResponse)
def confirm_reconciliation(
    request: ReconciliationConfirmRequest,
    db: Session = Depends(get_db),
):
    """確認結帳：批次將工單狀態從「已完成_待請款」更新為「已請款」"""
    
    if not request.work_order_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="請選擇至少一張工單進行結帳"
        )
    
    client = db.query(Client).filter(Client.id == request.client_id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="客戶不存在")

    year, month_num = parse_month(request.month)
    start_date, end_date = get_billing_period(year, month_num, client.billing_cycle)
    
    # 查詢目標工單
    query = db.query(WorkOrder).filter(
        WorkOrder.id.in_(request.work_order_ids),
        WorkOrder.client_id == request.client_id,
        WorkOrder.status == WorkOrderStatus.COMPLETED_PENDING_BILLING,
        WorkOrder.date >= start_date,
        WorkOrder.date <= end_date,
    )
    
    work_orders = query.all()
    
    if not work_orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到符合條件的待請款工單"
        )
    
    # 檢查是否有不符合條件的工單 ID
    found_ids = {wo.id for wo in work_orders}
    requested_ids = set(request.work_order_ids)
    missing_ids = requested_ids - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"以下工單不符合結帳條件（非待請款、非該客戶、非該月份）：{sorted(missing_ids)}"
        )
    
    lines = [{"order_id": w.id, "date": w.date.isoformat(), "item": w.item_name,
              "reference": w.client_order_no, "quantity": w.quantity, "amount": str(w.total_amount)}
             for w in sorted(work_orders, key=lambda w: (w.date, w.id))]
    total = sum(w.total_amount for w in work_orders)
    statement = Statement(client_id=client.id, client_name=client.name, month=request.month,
                          period_start=start_date, period_end=end_date, lines=lines, sources=[], total=total)
    try:
        db.add(statement)
        db.flush()
        for order in work_orders:
            db.add(IssuedOrder(order_id=order.id, statement_id=statement.id))
            order.status = WorkOrderStatus.BILLED
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "工單已出單，請重新整理")
    return ReconciliationConfirmResponse(success=True, statement_id=statement.id,
        message=f"已建立結算單 #{statement.id}", updated_count=len(lines), total_amount=total)


def statement_data(row):
    fields = ("id", "issued", "client_id", "client_name", "month", "period_start", "period_end",
              "sources", "merged_into", "lines")
    return {**{key: getattr(row, key) for key in fields}, "total": str(row.total)}


@router.get("/statements")
def statements(db: Session = Depends(get_db)):
    return [statement_data(row) for row in db.query(Statement).order_by(Statement.id.desc())]


class MergeRequest(BaseModel):
    ids: list[int]


@router.post("/statements/merge")
def merge_statements(request: MergeRequest, db: Session = Depends(get_db)):
    ids = set(request.ids)
    if len(ids) < 2 or len(ids) != len(request.ids):
        raise HTTPException(400, "請勾選至少兩張不同的結算單")
    rows = db.query(Statement).filter(Statement.id.in_(ids)).order_by(Statement.id).all()
    if len(rows) != len(ids) or any(row.merged_into for row in rows):
        raise HTTPException(409, "選取的單據不存在或已併單")
    first = rows[0]
    if len({(r.client_id, r.month, r.period_start, r.period_end) for r in rows}) != 1:
        raise HTTPException(400, "只能合併同客戶、同帳期的結算單")
    merged = Statement(client_id=first.client_id, client_name=first.client_name, month=first.month,
                       period_start=first.period_start, period_end=first.period_end,
                       sources=[r.id for r in rows], lines=[line for r in rows for line in r.lines],
                       total=sum(r.total for r in rows))
    db.add(merged)
    db.flush()
    claimed = db.query(Statement).filter(Statement.id.in_(ids), Statement.merged_into.is_(None)).update(
        {Statement.merged_into: merged.id}, synchronize_session=False)
    if claimed != len(ids):
        db.rollback()
        raise HTTPException(409, "單據已被合併，請重新整理")
    db.commit()
    return statement_data(merged)


@router.get("/months", response_model=List[str])
def get_available_months(
    client_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    """取得該客戶有待請款工單的月份清單（供前端下拉選單）"""
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客戶不存在"
        )
    
    # A late-month order belongs to the following billing period.
    order_dates = db.query(WorkOrder.date).filter(
        WorkOrder.client_id == client_id,
        WorkOrder.status == WorkOrderStatus.COMPLETED_PENDING_BILLING,
    ).all()
    
    return sorted(
        {billing_month_for_date(row.date, client.billing_cycle) for row in order_dates},
        reverse=True,
    )
