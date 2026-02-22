"""
ProductPricing model — Pricing layer for finished goods.

One pricing record per finished good per company.
Stores profit margin, cost basis (WAC snapshot), and selling price.
Status: "draft" (not for sale) or "listed" (available in Sales Orders).
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, UniqueConstraint
from app.database import Base


class ProductPricing(Base):
    __tablename__ = "product_pricing"
    __table_args__ = (
        UniqueConstraint("company_id", "item_id", name="uq_company_item_pricing"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    item_id = Column(String, ForeignKey("items.id"), nullable=False)

    profit_margin_percent = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)
    cost_basis = Column(Float, nullable=False, default=0.0)

    status = Column(String, default="draft")  # "draft" | "listed"
    notes = Column(String, nullable=True)

    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    updated_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
