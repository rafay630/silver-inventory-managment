"""Pydantic schemas for Product Pricing / Sales Catalog."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProductPricingCreate(BaseModel):
    item_id: str
    profit_margin_percent: float  # e.g. 25.0 for 25%
    notes: Optional[str] = None


class ProductPricingUpdate(BaseModel):
    profit_margin_percent: Optional[float] = None
    notes: Optional[str] = None


class ProductPricingOut(BaseModel):
    id: str
    item_id: str
    item_name: str
    item_sku: str
    profit_margin_percent: float
    cost_basis: float
    selling_price: float
    status: str
    notes: Optional[str] = None
    current_wac: float
    current_stock: float
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CatalogItem(BaseModel):
    """Full catalog entry — includes items with NO pricing record yet."""
    item_id: str
    item_name: str
    item_sku: str
    item_type: str
    current_wac: float
    current_stock: float
    # Pricing fields (None if no ProductPricing record exists)
    pricing_id: Optional[str] = None
    profit_margin_percent: Optional[float] = None
    cost_basis: Optional[float] = None
    selling_price: Optional[float] = None
    status: str = "draft"
    notes: Optional[str] = None
    updated_at: Optional[datetime] = None


class ListedItem(BaseModel):
    """Listed product for Sales Order dropdown."""
    item_id: str
    item_name: str
    item_sku: str
    selling_price: float
    current_stock: float
    current_wac: float
