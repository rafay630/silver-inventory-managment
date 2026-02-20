from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.inventory import WIPResponse, WIPStatusUpdate, FinishedGoodsResponse, TransactionResponse
from app.dependencies import get_current_user, require_roles
from app.models.inventory import WIPInventory, FinishedGoods, InventoryTransaction
from app.models.production import ProductionBatch
from app.models.product import Product
from app.models.raw_material import RawMaterial
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api", tags=["Inventory"])


# ─── WIP ───────────────────────────────────────────────
@router.get("/wip", response_model=List[WIPResponse])
def list_wip(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(WIPInventory).all()
    result = []
    for w in items:
        batch = db.query(ProductionBatch).filter(ProductionBatch.id == w.batch_id).first()
        product = db.query(Product).filter(Product.id == w.product_id).first()
        result.append(WIPResponse(
            id=w.id,
            batch_id=w.batch_id,
            batch_number=batch.batch_number if batch else None,
            product_id=w.product_id,
            product_name=product.name if product else None,
            quantity=w.quantity,
            status=w.status,
            updated_at=w.updated_at,
            created_at=w.created_at,
        ))
    return result


@router.get("/wip/{batch_id}", response_model=List[WIPResponse])
def get_wip_by_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(WIPInventory).filter(WIPInventory.batch_id == batch_id).all()
    result = []
    for w in items:
        batch = db.query(ProductionBatch).filter(ProductionBatch.id == w.batch_id).first()
        product = db.query(Product).filter(Product.id == w.product_id).first()
        result.append(WIPResponse(
            id=w.id,
            batch_id=w.batch_id,
            batch_number=batch.batch_number if batch else None,
            product_id=w.product_id,
            product_name=product.name if product else None,
            quantity=w.quantity,
            status=w.status,
            updated_at=w.updated_at,
            created_at=w.created_at,
        ))
    return result


@router.patch("/wip/{wip_id}/status", response_model=WIPResponse)
def update_wip_status(
    wip_id: UUID,
    data: WIPStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "production_manager"])),
):
    wip = db.query(WIPInventory).filter(WIPInventory.id == wip_id).first()
    if not wip:
        raise HTTPException(status_code=404, detail="WIP item not found")

    wip.status = data.status
    db.commit()
    db.refresh(wip)

    batch = db.query(ProductionBatch).filter(ProductionBatch.id == wip.batch_id).first()
    product = db.query(Product).filter(Product.id == wip.product_id).first()
    return WIPResponse(
        id=wip.id,
        batch_id=wip.batch_id,
        batch_number=batch.batch_number if batch else None,
        product_id=wip.product_id,
        product_name=product.name if product else None,
        quantity=wip.quantity,
        status=wip.status,
        updated_at=wip.updated_at,
        created_at=wip.created_at,
    )


# ─── FINISHED GOODS ───────────────────────────────────
@router.get("/finished-goods", response_model=List[FinishedGoodsResponse])
def list_finished_goods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(FinishedGoods).all()
    result = []
    for fg in items:
        product = db.query(Product).filter(Product.id == fg.product_id).first()
        batch = db.query(ProductionBatch).filter(ProductionBatch.id == fg.batch_id).first() if fg.batch_id else None
        result.append(FinishedGoodsResponse(
            id=fg.id,
            product_id=fg.product_id,
            product_name=product.name if product else None,
            batch_id=fg.batch_id,
            batch_number=batch.batch_number if batch else None,
            quantity=fg.quantity,
            location=fg.location,
            created_at=fg.created_at,
        ))
    return result


# ─── TRANSACTIONS ──────────────────────────────────────
@router.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = 0,
    limit: int = 50,
    transaction_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(InventoryTransaction)
    if transaction_type:
        query = query.filter(InventoryTransaction.transaction_type == transaction_type)
    txns = query.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for t in txns:
        rm = db.query(RawMaterial).filter(RawMaterial.id == t.raw_material_id).first() if t.raw_material_id else None
        product = db.query(Product).filter(Product.id == t.product_id).first() if t.product_id else None
        result.append(TransactionResponse(
            id=t.id,
            transaction_type=t.transaction_type,
            raw_material_id=t.raw_material_id,
            raw_material_name=rm.name if rm else None,
            product_id=t.product_id,
            product_name=product.name if product else None,
            batch_id=t.batch_id,
            quantity=t.quantity,
            unit=t.unit,
            reference_number=t.reference_number,
            notes=t.notes,
            created_by=t.created_by,
            created_at=t.created_at,
        ))
    return result
