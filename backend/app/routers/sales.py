"""Sales Router — Create sales orders."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sales import SalesOrder
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.sales import SalesOrderCreate, SalesOrderOut
from app.services.sales_service import SalesService
from typing import List, Optional

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.post("/", response_model=SalesOrderOut, status_code=201)
def create_sale(data: SalesOrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = SalesService.create_sale(
        db=db,
        company_id=user.company_id,
        customer_name=data.customer_name,
        order_date=data.order_date,
        items=[item.model_dump() for item in data.items],
        notes=data.notes,
        created_by=user.id,
    )
    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=List[SalesOrderOut])
def list_sales(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(SalesOrder).filter(SalesOrder.company_id == user.company_id)
    if status:
        q = q.filter(SalesOrder.status == status)
    return q.order_by(SalesOrder.created_at.desc()).all()


@router.get("/{order_id}", response_model=SalesOrderOut)
def get_sale(order_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(SalesOrder).filter(
        SalesOrder.id == order_id,
        SalesOrder.company_id == user.company_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Sales order not found")
    return order
