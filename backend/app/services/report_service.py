from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from app.models.raw_material import RawMaterial, RawMaterialStock
from app.models.production import ProductionBatch, ProductionBatchMaterial
from app.models.inventory import WIPInventory, FinishedGoods
from app.models.wastage import WastageRecord
from app.models.product import Product
from app.services.inventory_service import get_current_stock


def get_stock_report(db: Session):
    """Raw material stock report with status indicators."""
    materials = db.query(RawMaterial).all()
    result = []
    for m in materials:
        current = get_current_stock(db, m.id)
        reorder = m.reorder_level or Decimal("0")
        if current <= 0:
            status = "critical"
        elif current <= reorder:
            status = "low"
        else:
            status = "healthy"
        result.append({
            "material_name": m.name,
            "material_type": m.material_type,
            "unit": m.unit,
            "current_stock": current,
            "reorder_level": reorder,
            "status": status,
        })
    return result


def get_wastage_report(db: Session):
    """Wastage report per product/batch."""
    records = db.query(WastageRecord).all()
    result = []
    for r in records:
        batch = db.query(ProductionBatch).filter(ProductionBatch.id == r.batch_id).first()
        material = db.query(RawMaterial).filter(RawMaterial.id == r.raw_material_id).first()
        product = db.query(Product).filter(Product.id == batch.product_id).first() if batch else None
        result.append({
            "batch_number": batch.batch_number if batch else "N/A",
            "product_name": product.name if product else "N/A",
            "material_name": material.name if material else "N/A",
            "expected_wastage": r.expected_wastage or Decimal("0"),
            "actual_wastage": r.actual_wastage,
            "variance": r.variance,
            "variance_percent": r.variance_percent,
        })
    return result


def get_efficiency_report(db: Session):
    """Production efficiency report — actual vs planned."""
    batches = db.query(ProductionBatch).filter(ProductionBatch.status == "completed").all()
    result = []
    for b in batches:
        product = db.query(Product).filter(Product.id == b.product_id).first()
        efficiency = Decimal("0")
        if b.planned_quantity > 0:
            efficiency = (Decimal(str(b.completed_quantity)) / Decimal(str(b.planned_quantity))) * 100
        result.append({
            "batch_number": b.batch_number,
            "product_name": product.name if product else "N/A",
            "planned_quantity": b.planned_quantity,
            "completed_quantity": b.completed_quantity,
            "rejected_quantity": b.rejected_quantity,
            "efficiency_percent": round(efficiency, 2),
        })
    return result


def get_wip_summary(db: Session):
    """WIP summary grouped by product."""
    products = db.query(Product).all()
    result = []
    for p in products:
        wip_items = db.query(WIPInventory).filter(WIPInventory.product_id == p.id).all()
        if not wip_items:
            continue
        in_process = sum(w.quantity for w in wip_items if w.status == "in_process")
        completed = sum(w.quantity for w in wip_items if w.status == "completed")
        rejected = sum(w.quantity for w in wip_items if w.status == "rejected")
        result.append({
            "product_name": p.name,
            "total_in_process": in_process,
            "total_completed": completed,
            "total_rejected": rejected,
        })
    return result


def get_batch_history(db: Session):
    """Full batch history."""
    batches = db.query(ProductionBatch).order_by(ProductionBatch.created_at.desc()).all()
    result = []
    for b in batches:
        product = db.query(Product).filter(Product.id == b.product_id).first()
        result.append({
            "batch_number": b.batch_number,
            "product_name": product.name if product else "N/A",
            "planned_quantity": b.planned_quantity,
            "completed_quantity": b.completed_quantity,
            "rejected_quantity": b.rejected_quantity,
            "status": b.status,
            "started_at": b.started_at,
            "completed_at": b.completed_at,
        })
    return result


def get_consumption_variance(db: Session):
    """Consumption variance report — required vs actual per batch."""
    batch_materials = db.query(ProductionBatchMaterial).all()
    result = []
    for bm in batch_materials:
        batch = db.query(ProductionBatch).filter(ProductionBatch.id == bm.batch_id).first()
        material = db.query(RawMaterial).filter(RawMaterial.id == bm.raw_material_id).first()
        product = db.query(Product).filter(Product.id == batch.product_id).first() if batch else None

        variance = None
        variance_pct = None
        if bm.actual_quantity is not None and bm.required_quantity:
            variance = bm.actual_quantity - bm.required_quantity
            if bm.required_quantity > 0:
                variance_pct = (variance / bm.required_quantity) * 100

        result.append({
            "batch_number": batch.batch_number if batch else "N/A",
            "product_name": product.name if product else "N/A",
            "material_name": material.name if material else "N/A",
            "required_quantity": bm.required_quantity,
            "actual_quantity": bm.actual_quantity,
            "variance": variance,
            "variance_percent": variance_pct,
        })
    return result
