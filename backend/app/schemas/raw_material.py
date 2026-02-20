from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


class RawMaterialCreate(BaseModel):
    name: str
    material_type: str  # SILVER | BRASS
    unit: str = "grams"
    reorder_level: Decimal = Decimal("0")


class RawMaterialResponse(BaseModel):
    id: UUID
    name: str
    material_type: str
    unit: str
    reorder_level: Decimal
    current_stock: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseEntry(BaseModel):
    raw_material_id: UUID
    supplier_id: Optional[UUID] = None
    quantity: Decimal
    unit_price: Optional[Decimal] = None
    purchase_date: date
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustment(BaseModel):
    raw_material_id: UUID
    quantity: Decimal  # positive to add, negative to deduct
    notes: Optional[str] = None


class RawMaterialStockResponse(BaseModel):
    id: UUID
    raw_material_id: UUID
    supplier_id: Optional[UUID]
    quantity: Decimal
    unit_price: Optional[Decimal]
    purchase_date: date
    invoice_number: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
