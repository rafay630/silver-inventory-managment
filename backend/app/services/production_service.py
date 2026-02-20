import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.product import Product, BillOfMaterial
from app.models.production import ProductionBatch, ProductionBatchMaterial
from app.models.inventory import WIPInventory, FinishedGoods, InventoryTransaction
from app.services.inventory_service import deduct_stock, get_current_stock
from app.services.wastage_service import calculate_expected_wastage, record_expected_wastage, update_actual_wastage
from app.config import get_settings

settings = get_settings()


def generate_batch_number() -> str:
    """Generate a unique batch number with timestamp."""
    now = datetime.utcnow()
    return f"BATCH-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"


def create_production_batch(
    db: Session, product_id: UUID, planned_quantity: int, user_id: UUID, notes: str = None
) -> ProductionBatch:
    """
    Create a production batch:
    1. Validate product exists and has BOM
    2. Calculate required materials (with wastage)
    3. Validate sufficient stock
    4. Deduct raw materials
    5. Create WIP entry
    6. Log all transactions
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    bom_items = db.query(BillOfMaterial).filter(BillOfMaterial.product_id == product_id).all()
    if not bom_items:
        raise HTTPException(status_code=400, detail="Product has no Bill of Materials defined")

    # Create the batch
    batch = ProductionBatch(
        batch_number=generate_batch_number(),
        product_id=product_id,
        planned_quantity=planned_quantity,
        status="in_progress",
        created_by=user_id,
        notes=notes,
    )
    db.add(batch)
    db.flush()  # Get the batch ID

    # Process each BOM item
    for bom_item in bom_items:
        gross_required = bom_item.quantity_per_unit * planned_quantity
        wastage_pct = product.wastage_percent or Decimal("0")
        expected_wastage = calculate_expected_wastage(gross_required, wastage_pct)
        total_required = gross_required + expected_wastage

        # Validate stock
        current_stock = get_current_stock(db, bom_item.raw_material_id)
        if current_stock < total_required:
            db.rollback()
            from app.models.raw_material import RawMaterial
            material = db.query(RawMaterial).filter(RawMaterial.id == bom_item.raw_material_id).first()
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient {material.name}. Need {total_required}g, have {current_stock}g",
            )

        # Deduct stock
        deduct_stock(db, bom_item.raw_material_id, total_required, batch.id, user_id)

        # Record batch material
        batch_material = ProductionBatchMaterial(
            batch_id=batch.id,
            raw_material_id=bom_item.raw_material_id,
            required_quantity=total_required,
            wastage_expected=expected_wastage,
        )
        db.add(batch_material)

        # Record expected wastage
        record_expected_wastage(db, batch.id, bom_item.raw_material_id, expected_wastage)

    # Create WIP entry
    wip = WIPInventory(
        batch_id=batch.id,
        product_id=product_id,
        quantity=planned_quantity,
        status="in_process",
    )
    db.add(wip)

    # Log WIP transaction
    txn = InventoryTransaction(
        transaction_type="WIP_IN",
        product_id=product_id,
        batch_id=batch.id,
        quantity=planned_quantity,
        notes="Material moved to WIP",
        created_by=user_id,
    )
    db.add(txn)

    db.commit()
    db.refresh(batch)
    return batch


def complete_production_batch(
    db: Session, batch_id: UUID, completed_qty: int, rejected_qty: int,
    actual_wastage_map: dict, user_id: UUID, notes: str = None
) -> ProductionBatch:
    """
    Complete a production batch:
    1. Update batch status and quantities
    2. Update WIP status
    3. Create finished goods entry
    4. Record actual wastage
    5. Generate variance alerts if threshold exceeded
    """
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "in_progress":
        raise HTTPException(status_code=400, detail="Batch is not in progress")

    # Update batch
    batch.completed_quantity = completed_qty
    batch.rejected_quantity = rejected_qty
    batch.status = "completed"
    batch.completed_at = datetime.utcnow()
    if notes:
        batch.notes = (batch.notes or "") + f"\n{notes}"
    db.add(batch)

    # Update WIP
    wip = db.query(WIPInventory).filter(
        WIPInventory.batch_id == batch_id
    ).first()
    if wip:
        wip.status = "completed"
        wip.quantity = 0
        db.add(wip)

    # Create finished goods
    if completed_qty > 0:
        fg = FinishedGoods(
            product_id=batch.product_id,
            batch_id=batch.id,
            quantity=completed_qty,
        )
        db.add(fg)

        # Log transactions
        txn_wip_out = InventoryTransaction(
            transaction_type="WIP_OUT",
            product_id=batch.product_id,
            batch_id=batch.id,
            quantity=batch.planned_quantity,
            notes="WIP completed",
            created_by=user_id,
        )
        db.add(txn_wip_out)

        txn_fg_in = InventoryTransaction(
            transaction_type="FG_IN",
            product_id=batch.product_id,
            batch_id=batch.id,
            quantity=completed_qty,
            notes="Finished goods received",
            created_by=user_id,
        )
        db.add(txn_fg_in)

    # Record actual wastage
    alerts = []
    for material_id_str, actual_waste in actual_wastage_map.items():
        material_id = UUID(material_id_str) if isinstance(material_id_str, str) else material_id_str
        record = update_actual_wastage(db, batch_id, material_id, Decimal(str(actual_waste)))
        if record and record.variance_percent and abs(record.variance_percent) > Decimal(str(settings.WASTAGE_ALERT_THRESHOLD)):
            alerts.append({
                "batch_id": str(batch_id),
                "raw_material_id": str(material_id),
                "variance_percent": float(record.variance_percent),
                "message": f"Wastage variance {record.variance_percent}% exceeds threshold of {settings.WASTAGE_ALERT_THRESHOLD}%",
            })

        # Update batch material actual values
        batch_mat = db.query(ProductionBatchMaterial).filter(
            ProductionBatchMaterial.batch_id == batch_id,
            ProductionBatchMaterial.raw_material_id == material_id,
        ).first()
        if batch_mat:
            batch_mat.wastage_actual = Decimal(str(actual_waste))
            batch_mat.actual_quantity = batch_mat.required_quantity
            db.add(batch_mat)

    db.commit()
    db.refresh(batch)
    return batch


def cancel_production_batch(db: Session, batch_id: UUID, user_id: UUID) -> ProductionBatch:
    """Cancel a batch and return materials to stock."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "in_progress":
        raise HTTPException(status_code=400, detail="Only in-progress batches can be cancelled")

    batch.status = "cancelled"
    db.add(batch)

    # Return materials to stock
    from app.models.raw_material import RawMaterialStock
    from sqlalchemy import func as sql_func

    batch_materials = db.query(ProductionBatchMaterial).filter(
        ProductionBatchMaterial.batch_id == batch_id
    ).all()

    for bm in batch_materials:
        # Add back to stock
        stock_return = RawMaterialStock(
            raw_material_id=bm.raw_material_id,
            quantity=bm.required_quantity,
            purchase_date=sql_func.current_date(),
            notes=f"Returned from cancelled batch {batch.batch_number}",
        )
        db.add(stock_return)

        txn = InventoryTransaction(
            transaction_type="RETURN_FROM_PROD",
            raw_material_id=bm.raw_material_id,
            batch_id=batch_id,
            quantity=bm.required_quantity,
            notes=f"Material returned from cancelled batch",
            created_by=user_id,
        )
        db.add(txn)

    # Update WIP
    wip = db.query(WIPInventory).filter(WIPInventory.batch_id == batch_id).first()
    if wip:
        wip.status = "rejected"
        wip.quantity = 0
        db.add(wip)

    db.commit()
    db.refresh(batch)
    return batch
