"""Single administrator login backed by revocable server-side sessions."""

from datetime import datetime, timedelta
import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_auth_db
from app.core.passwords import verify_password
from app.models.auth_session import AuthSession, Employee


router = APIRouter()
COOKIE_NAME = "__Host-print_factory_session"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class LoginRequest(BaseModel):
    username: str = ""
    password: str


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def require_session(request: Request, db: Session = Depends(get_auth_db)) -> AuthSession:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="請先登入")

    session = db.query(AuthSession).filter(AuthSession.token_hash == _token_hash(token)).first()
    credential = get_settings().ADMIN_PASSWORD_HASH
    if session and session.employee is not None:
        employee = db.get(Employee, session.employee)
        if not employee or not employee.active:
            raise HTTPException(401, "帳號已停用")
        credential = employee.password_hash
    active_credential = hashlib.sha256(credential.encode()).hexdigest()
    if (
        session is None
        or session.expires_at <= datetime.utcnow()
        or not hmac.compare_digest(session.credential_hash, active_credential)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登入已過期，請重新登入")

    if request.method in UNSAFE_METHODS:
        csrf_token = request.headers.get("X-CSRF-Token", "")
        if not csrf_token or not hmac.compare_digest(csrf_token, session.csrf_token):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="安全驗證失敗，請重新整理頁面")

    return session


def require_admin(session: AuthSession = Depends(require_session)):
    if session.employee is not None:
        raise HTTPException(403, "僅限主管")
    return session


def identity(session):
    return {"role": "employee" if session.employee else "admin", "username": session.employee}


@router.get("/employee-names", response_model=list[str])
def employee_names(db: Session = Depends(get_auth_db)):
    return [name for (name,) in db.query(Employee.username).filter(Employee.active == 1).order_by(Employee.username)]


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_auth_db)):
    settings = get_settings()
    if not settings.ADMIN_PASSWORD_HASH:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="管理員密碼尚未設定")
    username = payload.username.strip()
    credential = settings.ADMIN_PASSWORD_HASH
    if username:
        employee = db.get(Employee, username)
        if not employee or not employee.active:
            raise HTTPException(401, "帳號或密碼錯誤")
        credential = employee.password_hash
    if not verify_password(payload.password, credential):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="密碼錯誤")

    token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=settings.SESSION_HOURS)
    db.add(
        AuthSession(
            token_hash=_token_hash(token),
            csrf_token=csrf_token,
            employee=username or None,
            credential_hash=hashlib.sha256(credential.encode("utf-8")).hexdigest(),
            expires_at=expires_at,
        )
    )
    db.commit()

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_HOURS * 3600,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return {"authenticated": True, "csrf_token": csrf_token, "role": "employee" if username else "admin", "username": username}


@router.get("/me")
def me(session: AuthSession = Depends(require_session)):
    return {"authenticated": True, "csrf_token": session.csrf_token, **identity(session)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, session: AuthSession = Depends(require_session), db: Session = Depends(get_auth_db)):
    db.delete(session)
    db.commit()
    response.delete_cookie(key=COOKIE_NAME, path="/", secure=True, httponly=True, samesite="strict")
