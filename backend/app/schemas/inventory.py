from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Category ──
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryOut(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ── UOM ──
class UOMCreate(BaseModel):
    name: str
    abbreviation: str

class UOMOut(BaseModel):
    id: str
    company_id: str
    name: str
    abbreviation: str
    created_at: datetime
    class Config:
        from_attributes = True


class UOMConversionCreate(BaseModel):
    from_uom_id: str
    to_uom_id: str
    conversion_factor: float

class UOMConversionOut(BaseModel):
    id: str
    company_id: str
    from_uom_id: str
    to_uom_id: str
    conversion_factor: float
    created_at: datetime
    class Config:
        from_attributes = True


# ── Item ──
class ItemCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    item_type: str  # raw_material | finished_good
    category_id: Optional[str] = None
    uom_id: str
    base_cost: float = 0
    reorder_level: float = 0

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    uom_id: Optional[str] = None
    base_cost: Optional[float] = None
    reorder_level: Optional[float] = None
    is_active: Optional[bool] = None

class ItemOut(BaseModel):
    id: str
    company_id: str
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    item_type: str
    category_id: Optional[str] = None
    uom_id: str
    base_cost: float
    reorder_level: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ── Warehouse ──
class WarehouseCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class WarehouseOut(BaseModel):
    id: str
    company_id: str
    name: str
    code: str
    address: Optional[str] = None
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ── Stock Ledger ──
class StockLedgerOut(BaseModel):
    id: str
    company_id: str
    item_id: str
    warehouse_id: str
    qty_in: float
    qty_out: float
    unit_cost: float
    reference_type: str
    reference_id: str
    description: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class StockBalanceOut(BaseModel):
    item_id: str
    item_name: str
    warehouse_id: str
    warehouse_name: str
    balance: float
    weighted_avg_cost: float
    total_value: float
