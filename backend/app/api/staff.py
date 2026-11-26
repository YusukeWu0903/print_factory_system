from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.auth import require_admin, require_session
from app.core.database import get_auth_db
from app.core.passwords import hash_password
from app.models.auth_session import AuthSession, Employee
from app.models.work_order import WorkOrder

from app.schemas.work_order import PieceName

router = APIRouter()

class Account(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=128)

class AccountChange(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)
    active: bool | None = None

@router.get("/accounts", dependencies=[Depends(require_admin)])
def accounts(db: Session = Depends(get_auth_db)):
    return [{"username": e.username, "active": bool(e.active)} for e in db.query(Employee).order_by(Employee.username)]

@router.post("/accounts", dependencies=[Depends(require_admin)], status_code=201)
def add(data: Account, db: Session = Depends(get_auth_db)):
    name = data.username.strip()
    if not name:
        raise HTTPException(422, "請填寫帳號")
    db.add(Employee(username=name, password_hash=hash_password(data.password)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "帳號已存在")
    return {"username": name}

@router.patch("/accounts", dependencies=[Depends(require_admin)])
def change(username: str, data: AccountChange, db: Session = Depends(get_auth_db)):
    e = db.get(Employee, username)
    if not e:
        raise HTTPException(404, "查無帳號")
    if data.password:
        e.password_hash = hash_password(data.password)
    if data.active is not None:
        e.active = int(data.active)
    db.query(AuthSession).filter_by(employee=username).delete()
    db.commit()
    return {"username":username}

def worker(session: AuthSession = Depends(require_session)):
    if not session.employee:
        raise HTTPException(403, "請使用員工帳號")
    return session.employee

def summary(w):
    return {"combined": w.combined, "piece_reports": w.piece_reports, **{key:getattr(w,key) for key in ('press_size', 'press_actual', 'press_waste', 'press_runs', 'press_ink', 'finisher', 'due_date', 'front_side', 'back_side', 'notes')}, "id":w.id,"item_name":w.item_name,"date":w.date,"client":w.client.name,
            "quantity":w.quantity,"completed_quantity":w.completed_quantity,"revision":w.revision}

@router.get("/orders", dependencies=[Depends(worker)])
def orders(db: Session = Depends(get_auth_db)):
    return [summary(w) for w in db.query(WorkOrder).order_by(WorkOrder.date.desc(), WorkOrder.id.desc())]

class Completion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    completed_quantity: int = Field(strict=True, ge=0, le=2147483647)
    revision: int = Field(ge=1)
    piece: PieceName | None = None

@router.patch("/orders/{oid}")
def complete(oid: int, data: Completion, username: str = Depends(worker), db: Session = Depends(get_auth_db)):
    w = db.get(WorkOrder, oid)
    if not w:
        raise HTTPException(404, "查無工單")
    if w.revision != data.revision:
        raise HTTPException(409, "工單已更新，請重新載入核對")
    db.info["actor"] = "師傅：" + username
    if bool(w.combined) != bool(data.piece):
        raise HTTPException(422, "請依工單版型選擇回報印件")
    if data.piece:
        w.piece_reports = {**(w.piece_reports or {}), data.piece: data.completed_quantity}
    else:
        w.completed_quantity = data.completed_quantity
    db.commit()
    return summary(w)
