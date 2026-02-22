from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ── Sales Order ──
class SalesOrderItemCreate(BaseModel):
    item_id: str
    warehouse_id: str
    quantity: float
    unit_price: float

class SalesOrderCreate(BaseModel):
    customer_name: str
    order_date: date
    notes: Optional[str] = None
    items: List[SalesOrderItemCreate]

class SalesOrderItemOut(BaseModel):
    id: str
    item_id: str
    warehouse_id: str
    quantity: float
    unit_price: float
    unit_cost: float
    total_price: float
    class Config:
        from_attributes = True

class SalesOrderOut(BaseModel):
    id: str
    company_id: str
    order_number: str
    customer_name: str
    order_date: date
    status: str
    total_amount: float
    total_cost: float
    notes: Optional[str] = None
    journal_entry_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    items: List[SalesOrderItemOut] = []
    class Config:
        from_attributes = True
