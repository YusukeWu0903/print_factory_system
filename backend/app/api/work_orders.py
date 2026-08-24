# print_factory_system/backend/app/api/work_orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.core.database import get_db
from app.models.work_order import WorkOrder, WorkOrderStatus
from app.models.client import Client
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderStatusUpdate,
    WorkOrderResponse,
    WorkOrderListResponse,
)

router = APIRouter()


def calculate_total(paper_fee: Decimal, plate_fee: Decimal, wage: Decimal, quantity: int) -> Decimal:
    """計算總金額：(紙錢 + 版費 + 印工) * 數量"""
    return (paper_fee + plate_fee + wage) * quantity


@router.post("/", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(work_order: WorkOrderCreate, db: Session = Depends(get_db)):
    # Verify client exists
    client = db.query(Client).filter(Client.id == work_order.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客戶不存在",
        )

    # Calculate total amount
    total_amount = calculate_total(
        work_order.paper_fee,
        work_order.plate_fee,
        work_order.wage,
        work_order.quantity,
    )

    db_work_order = WorkOrder(
        **work_order.model_dump(),
        total_amount=total_amount,
        status=WorkOrderStatus.PRINTING,
    )
    db.add(db_work_order)
    db.commit()
    db.refresh(db_work_order)

    # Add client name for response
    return WorkOrderResponse.from_orm_with_client(db_work_order)


@router.get("/", response_model=List[WorkOrderListResponse])
def list_work_orders(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    client_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    query = db.query(WorkOrder).options(joinedload(WorkOrder.client))

    if status:
        try:
            status_enum = WorkOrderStatus(status)
            query = query.filter(WorkOrder.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的狀態值：{status}",
            )
    if client_id:
        query = query.filter(WorkOrder.client_id == client_id)
    if start_date:
        query = query.filter(WorkOrder.date >= start_date)
    if end_date:
        query = query.filter(WorkOrder.date <= end_date)

    query = query.order_by(WorkOrder.date.desc(), WorkOrder.id.desc())
    work_orders = query.offset(skip).limit(limit).all()

    return [
        WorkOrderListResponse(
            id=wo.id,
            date=wo.date,
            client_name=wo.client.name if wo.client else "未知客戶",
            client_id=wo.client_id,
            item_name=wo.item_name,
            quantity=wo.quantity,
            total_amount=wo.total_amount,
            status=wo.status.value if hasattr(wo.status, 'value') else str(wo.status),
        )
        for wo in work_orders
    ]


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
def get_work_order(work_order_id: int, db: Session = Depends(get_db)):
    work_order = (
        db.query(WorkOrder)
        .options(joinedload(WorkOrder.client))
        .filter(WorkOrder.id == work_order_id)
        .first()
    )
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工單不存在",
        )

    return WorkOrderResponse.from_orm_with_client(work_order)


@router.patch("/{work_order_id}", response_model=WorkOrderResponse)
def update_work_order(
    work_order_id: int, work_order_update: WorkOrderUpdate, db: Session = Depends(get_db)
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工單不存在",
        )

    update_data = work_order_update.model_dump(exclude_unset=True)

    # Verify client exists if client_id is being updated
    if "client_id" in update_data:
        client = db.query(Client).filter(Client.id == update_data["client_id"]).first()
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="客戶不存在",
            )

    # Recalculate total if any fee/quantity changed
    fee_fields = ["paper_fee", "plate_fee", "wage", "quantity"]
    if any(field in update_data for field in fee_fields):
        paper_fee = update_data.get("paper_fee", work_order.paper_fee)
        plate_fee = update_data.get("plate_fee", work_order.plate_fee)
        wage = update_data.get("wage", work_order.wage)
        quantity = update_data.get("quantity", work_order.quantity)
        update_data["total_amount"] = calculate_total(paper_fee, plate_fee, wage, quantity)

    for field, value in update_data.items():
        setattr(work_order, field, value)

    db.commit()
    db.refresh(work_order)

    return WorkOrderResponse.from_orm_with_client(work_order)


@router.patch("/{work_order_id}/status", response_model=WorkOrderResponse)
def update_work_order_status(
    work_order_id: int, status_update: WorkOrderStatusUpdate, db: Session = Depends(get_db)
):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工單不存在",
        )

    # Status transition validation (防呆機制)
    current_status = work_order.status
    # Convert string to enum
    try:
        new_status = WorkOrderStatus(status_update.status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"無效的狀態值：{status_update.status}",
        )

    # Define allowed transitions
    allowed_transitions = {
        WorkOrderStatus.PRINTING: [WorkOrderStatus.COMPLETED_PENDING_BILLING],
        WorkOrderStatus.COMPLETED_PENDING_BILLING: [WorkOrderStatus.BILLED, WorkOrderStatus.PRINTING],
        WorkOrderStatus.BILLED: [WorkOrderStatus.COMPLETED_PENDING_BILLING],  # Allow rollback for corrections
    }

    if new_status not in allowed_transitions.get(current_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不允許的狀態變更：{current_status.value} -> {new_status.value}",
        )

    work_order.status = new_status
    db.commit()
    db.refresh(work_order)

    return WorkOrderResponse.from_orm_with_client(work_order)


@router.delete("/{work_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_order(work_order_id: int, db: Session = Depends(get_db)):
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="工單不存在",
        )

    # Only allow deletion of PRINTING status orders
    if work_order.status != WorkOrderStatus.PRINTING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能刪除「印製中」狀態的工單",
        )

    db.delete(work_order)
    db.commit()
    return None