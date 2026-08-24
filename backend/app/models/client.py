# print_factory_system/backend/app/models/client.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    tax_id = Column(String(20), nullable=True, unique=True, index=True)
    billing_cycle = Column(Integer, nullable=False, default=1)  # 結帳日 (1-31)

    # Relationship
    work_orders = relationship("WorkOrder", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', tax_id='{self.tax_id}', billing_cycle={self.billing_cycle})>"