import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Item(Base):
    """
    Unified Item Master — covers both Raw Materials and Finished Goods.
    Stock is NEVER stored here. Stock = SUM(qty_in - qty_out) from stock_ledger.
    """
    __tablename__ = "items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), index=True)
    barcode = Column(String(100), index=True)
    description = Column(Text)
    item_type = Column(String(30), nullable=False, index=True)
    # item_type: 'raw_material' or 'finished_good'
    category_id = Column(String(36), ForeignKey("categories.id"), index=True)
    uom_id = Column(String(36), ForeignKey("uom.id"), nullable=False)
    base_cost = Column(Numeric(18, 4), default=0)
    reorder_level = Column(Numeric(15, 4), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company")
    category = relationship("Category")
    uom = relationship("UOM")

    __table_args__ = (
        Index("ix_items_company_sku", "company_id", "sku", unique=True),
        Index("ix_items_company_barcode", "company_id", "barcode", unique=True),
        Index("ix_items_company_type", "company_id", "item_type"),
    )
