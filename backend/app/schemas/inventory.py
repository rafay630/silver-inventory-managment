from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class WIPResponse(BaseModel):
    id: UUID
    batch_id: UUID
    batch_number: Optional[str] = None
    product_id: UUID
    product_name: Optional[str] = None
    quantity: Decimal
    status: str
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class WIPStatusUpdate(BaseModel):
    status: str  # in_process | completed | rejected


class FinishedGoodsResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: Optional[str] = None
    batch_id: Optional[UUID]
    batch_number: Optional[str] = None
    quantity: Decimal
    location: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: UUID
    transaction_type: str
    raw_material_id: Optional[UUID]
    raw_material_name: Optional[str] = None
    product_id: Optional[UUID]
    product_name: Optional[str] = None
    batch_id: Optional[UUID]
    quantity: Decimal
    unit: Optional[str]
    reference_number: Optional[str]
    notes: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True
