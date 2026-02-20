from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.dependencies import get_current_user, require_roles
from app.models.supplier import Supplier
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/suppliers", tags=["Suppliers"])


@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Supplier).filter(Supplier.is_active == True).all()


@router.post("/", response_model=SupplierResponse)
def create_supplier(
    data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "store_manager"])),
):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "store_manager"])),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, key, value)

    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def deactivate_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    supplier.is_active = False
    db.commit()
    return {"detail": "Supplier deactivated"}
