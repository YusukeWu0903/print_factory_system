# print_factory_system/backend/app/api/reconciliation.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.core.database import get_db
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.client import Client
from pydantic import BaseModel
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

    class Config:
        from_attributes = True


class ReconciliationSummary(BaseModel):
    client_id: int
    client_name: str
    month: str  # "2026-08"
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
    updated_count: int
    total_amount: Decimal


# ===== Helper Functions =====

def parse_month(month_str: str) -> tuple:
    """解析 '2026-08' 格式，回傳 (year, month)"""
    try:
        year, month = map(int, month_str.split('-'))
        if not (1 <= month <= 12):
            raise ValueError
        return year, month
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="月份格式錯誤，請使用 YYYY-MM 格式（如 2026-08）"
        )


def get_month_date_range(year: int, month: int) -> tuple:
    """取得該月份的起始/結束日期"""
    from calendar import monthrange
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    return start_date, end_date


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
    start_date, end_date = get_month_date_range(year, month_num)
    
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
    
    year, month_num = parse_month(request.month)
    start_date, end_date = get_month_date_range(year, month_num)
    
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
            detail="找到符合條件的待請款工單"
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
    
    # 批次更新狀態
    updated_count = 0
    total_amount = Decimal('0')
    
    try:
        for wo in work_orders:
            wo.status = WorkOrderStatus.BILLED
            total_amount += wo.total_amount
            updated_count += 1
        
        db.commit()
        
        return ReconciliationConfirmResponse(
            success=True,
            message=f"成功結帳 {updated_count} 張工單",
            updated_count=updated_count,
            total_amount=total_amount,
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"結帳失敗：{str(e)}"
        )


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
    
    # 查詢有「已完成_待請款」工單的月份
    months = db.query(
        extract('year', WorkOrder.date).label('year'),
        extract('month', WorkOrder.date).label('month')
    ).filter(
        WorkOrder.client_id == client_id,
        WorkOrder.status == WorkOrderStatus.COMPLETED_PENDING_BILLING,
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    return [f"{int(m.year)}-{int(m.month):02d}" for m in months]