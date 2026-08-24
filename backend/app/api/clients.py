# print_factory_system/backend/app/api/clients.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse

router = APIRouter()


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    # Check if tax_id already exists
    if client.tax_id:
        existing = db.query(Client).filter(Client.tax_id == client.tax_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="統一編號已存在",
            )

    db_client = Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return ClientResponse.from_orm_without_orders(db_client)


@router.get("/", response_model=List[ClientResponse])
def list_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    clients = db.query(Client).offset(skip).limit(limit).all()
    return [ClientResponse.from_orm_without_orders(c) for c in clients]


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客戶不存在",
        )
    return ClientResponse.from_orm_without_orders(client)


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(client_id: int, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客戶不存在",
        )

    update_data = client_update.model_dump(exclude_unset=True)

    # Check tax_id uniqueness if updating
    if "tax_id" in update_data and update_data["tax_id"]:
        existing = db.query(Client).filter(
            Client.tax_id == update_data["tax_id"], Client.id != client_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="統一編號已存在",
            )

    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return ClientResponse.from_orm_without_orders(client)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="客戶不存在",
        )

    # Check if client has work orders
    if client.work_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="該客戶仍有關聯工單，無法刪除",
        )

    db.delete(client)
    db.commit()
    return None