from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.raw_material import RawMaterialCreate, RawMaterialResponse, PurchaseEntry, StockAdjustment, RawMaterialStockResponse
from app.dependencies import get_current_user, require_roles
from app.models.raw_material import RawMaterial, RawMaterialStock
from app.models.user import User
from app.services.inventory_service import get_current_stock, record_purchase, adjust_stock
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/raw-materials", tags=["Raw Materials"])


@router.get("/", response_model=List[RawMaterialResponse])
def list_raw_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    materials = db.query(RawMaterial).all()
    result = []
    for m in materials:
        stock = get_current_stock(db, m.id)
        result.append(RawMaterialResponse(
            id=m.id,
            name=m.name,
            material_type=m.material_type,
            unit=m.unit,
            reorder_level=m.reorder_level,
            current_stock=stock,
            created_at=m.created_at,
        ))
    return result


@router.post("/", response_model=RawMaterialResponse)
def create_raw_material(
    data: RawMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    material = RawMaterial(**data.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return RawMaterialResponse(
        id=material.id,
        name=material.name,
        material_type=material.material_type,
        unit=material.unit,
        reorder_level=material.reorder_level,
        current_stock=0,
        created_at=material.created_at,
    )


@router.post("/purchase", response_model=RawMaterialStockResponse)
def create_purchase(
    data: PurchaseEntry,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "store_manager"])),
):
    # Verify raw material exists
    material = db.query(RawMaterial).filter(RawMaterial.id == data.raw_material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")
    return record_purchase(db, data, current_user.id)


@router.post("/adjust")
def create_adjustment(
    data: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "store_manager"])),
):
    # Verify raw material exists
    material = db.query(RawMaterial).filter(RawMaterial.id == data.raw_material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")
    new_stock = adjust_stock(db, data, current_user.id)
    return {"detail": "Stock adjusted", "new_stock": float(new_stock)}
