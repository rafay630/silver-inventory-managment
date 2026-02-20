from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from decimal import Decimal
from uuid import UUID
from app.models.raw_material import RawMaterial, RawMaterialStock
from app.models.inventory import InventoryTransaction, WIPInventory, FinishedGoods
from app.schemas.raw_material import PurchaseEntry, StockAdjustment
from fastapi import HTTPException


def get_current_stock(db: Session, raw_material_id: UUID) -> Decimal:
    """Calculate current stock for a raw material from all stock entries."""
    result = db.query(sql_func.coalesce(sql_func.sum(RawMaterialStock.quantity), 0)).filter(
        RawMaterialStock.raw_material_id == raw_material_id
    ).scalar()
    return Decimal(str(result))


def record_purchase(db: Session, purchase: PurchaseEntry, user_id: UUID) -> RawMaterialStock:
    """Record a raw material purchase and create inventory transaction."""
    stock_entry = RawMaterialStock(
        raw_material_id=purchase.raw_material_id,
        supplier_id=purchase.supplier_id,
        quantity=purchase.quantity,
        unit_price=purchase.unit_price,
        purchase_date=purchase.purchase_date,
        invoice_number=purchase.invoice_number,
        notes=purchase.notes,
    )
    db.add(stock_entry)

    # Log the transaction
    txn = InventoryTransaction(
        transaction_type="PURCHASE",
        raw_material_id=purchase.raw_material_id,
        quantity=purchase.quantity,
        reference_number=purchase.invoice_number,
        notes=purchase.notes,
        created_by=user_id,
    )
    db.add(txn)
    db.commit()
    db.refresh(stock_entry)
    return stock_entry


def adjust_stock(db: Session, adjustment: StockAdjustment, user_id: UUID) -> Decimal:
    """Adjust stock (positive to add, negative to deduct). Prevents negative stock."""
    current = get_current_stock(db, adjustment.raw_material_id)
    new_stock = current + adjustment.quantity

    if new_stock < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Current: {current}, Adjustment: {adjustment.quantity}",
        )

    # Create an adjustment stock entry
    stock_entry = RawMaterialStock(
        raw_material_id=adjustment.raw_material_id,
        quantity=adjustment.quantity,
        purchase_date=sql_func.current_date(),
        notes=f"Stock Adjustment: {adjustment.notes or 'Manual adjustment'}",
    )
    db.add(stock_entry)

    txn = InventoryTransaction(
        transaction_type="ADJUSTMENT",
        raw_material_id=adjustment.raw_material_id,
        quantity=adjustment.quantity,
        notes=adjustment.notes,
        created_by=user_id,
    )
    db.add(txn)
    db.commit()
    return new_stock


def deduct_stock(db: Session, raw_material_id: UUID, quantity: Decimal, batch_id: UUID, user_id: UUID):
    """Deduct stock for production. Validates sufficient stock exists."""
    current = get_current_stock(db, raw_material_id)
    if current < quantity:
        material = db.query(RawMaterial).filter(RawMaterial.id == raw_material_id).first()
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient {material.name} stock. Need {quantity}{material.unit}, have {current}{material.unit}",
        )

    # Negative stock entry to deduct
    stock_entry = RawMaterialStock(
        raw_material_id=raw_material_id,
        quantity=-quantity,
        purchase_date=sql_func.current_date(),
        notes=f"Issued to production batch",
    )
    db.add(stock_entry)

    txn = InventoryTransaction(
        transaction_type="ISSUE_TO_PROD",
        raw_material_id=raw_material_id,
        batch_id=batch_id,
        quantity=quantity,
        notes="Material issued to production",
        created_by=user_id,
    )
    db.add(txn)
