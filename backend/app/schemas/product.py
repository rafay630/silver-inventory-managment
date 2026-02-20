from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class BOMItemCreate(BaseModel):
    raw_material_id: UUID
    quantity_per_unit: Decimal


class BOMItemUpdate(BaseModel):
    quantity_per_unit: Optional[Decimal] = None


class BOMItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    raw_material_id: UUID
    raw_material_name: Optional[str] = None
    raw_material_type: Optional[str] = None
    quantity_per_unit: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    wastage_percent: Decimal = Decimal("0")
    unit: str = "pieces"


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    wastage_percent: Optional[Decimal] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    sku: Optional[str]
    description: Optional[str]
    wastage_percent: Decimal
    unit: str
    is_active: bool
    bom_items: Optional[List[BOMItemResponse]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
