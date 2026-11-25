from datetime import date

from sqlalchemy import Column, Date, Integer, JSON, Numeric, String
from app.core.database import Base


class Statement(Base):
    __tablename__ = "statements"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False, index=True)
    client_name = Column(String, nullable=False)
    month = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    issued = Column(Date, default=date.today, nullable=False)
    lines = Column(JSON, nullable=False)
    sources = Column(JSON, nullable=False)
    merged_into = Column(Integer)
    total = Column(Numeric(18, 2), nullable=False)


class IssuedOrder(Base):
    __tablename__ = "issued_orders"
    order_id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, nullable=False)
