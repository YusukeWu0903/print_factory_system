from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    employee = Column(String(50), nullable=True)
    csrf_token = Column(String(64), nullable=False)
    credential_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)


class Employee(Base):
    __tablename__ = "employees"
    username = Column(String(50), primary_key=True)
    password_hash = Column(String(256), nullable=False)
    active = Column(Integer, nullable=False, default=1)
