from pydantic import BaseModel
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class BatchCreate(BaseModel):
    product_id: UUID
    planned_quantity: int
    notes: Optional[str] = None


class BatchComplete(BaseModel):
    completed_quantity: int
    rejected_quantity: int = 0
    actual_wastage: Dict[str, Decimal] = {}  # raw_material_id -> actual wastage amount
    notes: Optional[str] = None


class BatchMaterialResponse(BaseModel):
    id: UUID
    batch_id: UUID
    raw_material_id: UUID
    raw_material_name: Optional[str] = None
    required_quantity: Decimal
    actual_quantity: Optional[Decimal]
    wastage_expected: Optional[Decimal]
    wastage_actual: Optional[Decimal]

    class Config:
        from_attributes = True


class BatchResponse(BaseModel):
    id: UUID
    batch_number: str
    product_id: UUID
    product_name: Optional[str] = None
    planned_quantity: int
    completed_quantity: int
    rejected_quantity: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    created_by: Optional[UUID]
    notes: Optional[str]
    materials: Optional[List[BatchMaterialResponse]] = None
    created_at: datetime

    class Config:
        from_attributes = True
