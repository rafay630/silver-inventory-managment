from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class StockReportItem(BaseModel):
    material_name: str
    material_type: str
    unit: str
    current_stock: Decimal
    reorder_level: Decimal
    status: str  # healthy | low | critical


class WastageReportItem(BaseModel):
    batch_number: str
    product_name: str
    material_name: str
    expected_wastage: Decimal
    actual_wastage: Optional[Decimal]
    variance: Optional[Decimal]
    variance_percent: Optional[Decimal]


class EfficiencyReportItem(BaseModel):
    batch_number: str
    product_name: str
    planned_quantity: int
    completed_quantity: int
    rejected_quantity: int
    efficiency_percent: Decimal


class WIPSummaryItem(BaseModel):
    product_name: str
    total_in_process: Decimal
    total_completed: Decimal
    total_rejected: Decimal


class ConsumptionVarianceItem(BaseModel):
    batch_number: str
    product_name: str
    material_name: str
    required_quantity: Decimal
    actual_quantity: Optional[Decimal]
    variance: Optional[Decimal]
    variance_percent: Optional[Decimal]
