from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ── BOM ──
class BOMItemCreate(BaseModel):
    raw_item_id: str
    quantity: float
    wastage_percent: float = 0
    uom_id: Optional[str] = None
    conversion_factor: float = 1

class BOMItemOut(BaseModel):
    id: str
    raw_item_id: str
    quantity: float
    wastage_percent: float
    uom_id: Optional[str] = None
    conversion_factor: float
    class Config:
        from_attributes = True

class BOMCreate(BaseModel):
    product_id: str
    version: str = "1.0"
    is_active: bool = True
    notes: Optional[str] = None
    items: List[BOMItemCreate]

class BOMOut(BaseModel):
    id: str
    company_id: str
    product_id: str
    version: str
    is_active: bool
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    items: List[BOMItemOut] = []
    class Config:
        from_attributes = True


# ── Production Order ──
class ProductionOrderCreate(BaseModel):
    product_id: str
    bom_id: str
    order_qty: float
    warehouse_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

class ProductionRequirementOut(BaseModel):
    id: str
    item_id: str
    required_qty: float
    available_qty: float
    status: str
    class Config:
        from_attributes = True

class ProductionOrderOut(BaseModel):
    id: str
    company_id: str
    order_number: str
    product_id: str
    bom_id: str
    order_qty: float
    completed_qty: float
    warehouse_id: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    requirements: List[ProductionRequirementOut] = []
    class Config:
        from_attributes = True


# ── WIP Issue ──
class WIPIssueItemCreate(BaseModel):
    item_id: str
    warehouse_id: str
    quantity: float

class WIPIssueCreate(BaseModel):
    production_order_id: str
    issue_date: date
    items: List[WIPIssueItemCreate]

class WIPIssueItemOut(BaseModel):
    id: str
    item_id: str
    warehouse_id: str
    quantity: float
    unit_cost: float
    total_cost: float
    class Config:
        from_attributes = True

class WIPIssueOut(BaseModel):
    id: str
    company_id: str
    production_order_id: str
    issue_number: str
    issue_date: date
    journal_entry_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    items: List[WIPIssueItemOut] = []
    class Config:
        from_attributes = True


# ── Production Expense ──
class ProductionExpenseCreate(BaseModel):
    production_order_id: str
    expense_type: str
    description: Optional[str] = None
    amount: float
    expense_date: date

class ProductionExpenseOut(BaseModel):
    id: str
    company_id: str
    production_order_id: str
    expense_type: str
    description: Optional[str] = None
    amount: float
    expense_date: date
    journal_entry_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ── Production Completion ──
class ProductionCompletionRequest(BaseModel):
    completed_qty: float
    completion_date: date
