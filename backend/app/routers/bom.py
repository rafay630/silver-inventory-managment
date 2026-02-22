"""BOM Router — Bill of Materials management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.bom import BOM
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.production import BOMCreate, BOMOut
from app.services.bom_service import BOMService
from typing import List, Optional

router = APIRouter(prefix="/api/bom", tags=["Bill of Materials"])


@router.post("/", response_model=BOMOut, status_code=201)
def create_bom(data: BOMCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bom = BOMService.create_bom(
        db=db,
        company_id=user.company_id,
        product_id=data.product_id,
        version=data.version,
        is_active=data.is_active,
        notes=data.notes,
        items=[item.model_dump() for item in data.items],
        created_by=user.id,
    )
    db.commit()
    db.refresh(bom)
    return bom


@router.get("/", response_model=List[BOMOut])
def list_boms(
    product_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(BOM).filter(BOM.company_id == user.company_id)
    if product_id:
        q = q.filter(BOM.product_id == product_id)
    if is_active is not None:
        q = q.filter(BOM.is_active == is_active)
    return q.order_by(BOM.created_at.desc()).all()


@router.get("/{bom_id}", response_model=BOMOut)
def get_bom(bom_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bom = db.query(BOM).filter(BOM.id == bom_id, BOM.company_id == user.company_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    return bom


@router.get("/{bom_id}/requirements")
def calculate_requirements(
    bom_id: str,
    order_qty: float,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Preview material requirements for a given order quantity."""
    return BOMService.calculate_requirements(db, bom_id, order_qty)
