from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.production import BatchCreate, BatchComplete, BatchResponse, BatchMaterialResponse
from app.dependencies import get_current_user, require_roles
from app.models.production import ProductionBatch, ProductionBatchMaterial
from app.models.product import Product
from app.models.raw_material import RawMaterial
from app.models.user import User
from app.services.production_service import (
    create_production_batch,
    complete_production_batch,
    cancel_production_batch,
)
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/production", tags=["Production"])


def _build_batch_response(batch: ProductionBatch, db: Session) -> BatchResponse:
    product = db.query(Product).filter(Product.id == batch.product_id).first()
    materials = []
    for bm in batch.materials:
        rm = db.query(RawMaterial).filter(RawMaterial.id == bm.raw_material_id).first()
        materials.append(BatchMaterialResponse(
            id=bm.id,
            batch_id=bm.batch_id,
            raw_material_id=bm.raw_material_id,
            raw_material_name=rm.name if rm else None,
            required_quantity=bm.required_quantity,
            actual_quantity=bm.actual_quantity,
            wastage_expected=bm.wastage_expected,
            wastage_actual=bm.wastage_actual,
        ))
    return BatchResponse(
        id=batch.id,
        batch_number=batch.batch_number,
        product_id=batch.product_id,
        product_name=product.name if product else None,
        planned_quantity=batch.planned_quantity,
        completed_quantity=batch.completed_quantity,
        rejected_quantity=batch.rejected_quantity,
        status=batch.status,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        created_by=batch.created_by,
        notes=batch.notes,
        materials=materials,
        created_at=batch.created_at,
    )


@router.get("/batches", response_model=List[BatchResponse])
def list_batches(
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ProductionBatch)
    if status:
        query = query.filter(ProductionBatch.status == status)
    batches = query.order_by(ProductionBatch.created_at.desc()).all()
    return [_build_batch_response(b, db) for b in batches]


@router.post("/batches", response_model=BatchResponse)
def create_batch(
    data: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "production_manager"])),
):
    batch = create_production_batch(
        db, data.product_id, data.planned_quantity, current_user.id, data.notes
    )
    return _build_batch_response(batch, db)


@router.get("/batches/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _build_batch_response(batch, db)


@router.patch("/batches/{batch_id}/complete", response_model=BatchResponse)
def complete_batch(
    batch_id: UUID,
    data: BatchComplete,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "production_manager"])),
):
    batch = complete_production_batch(
        db, batch_id, data.completed_quantity, data.rejected_quantity,
        data.actual_wastage, current_user.id, data.notes,
    )
    return _build_batch_response(batch, db)


@router.patch("/batches/{batch_id}/cancel", response_model=BatchResponse)
def cancel_batch(
    batch_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "production_manager"])),
):
    batch = cancel_production_batch(db, batch_id, current_user.id)
    return _build_batch_response(batch, db)
