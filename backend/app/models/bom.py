import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class BOM(Base):
    """Bill of Materials with versioning. Only one active BOM per product."""
    __tablename__ = "boms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False, default="1.0")
    is_active = Column(Boolean, default=True)
    notes = Column(String(500))
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company")
    product = relationship("Item", foreign_keys=[product_id])
    creator = relationship("User")
    items = relationship("BOMItem", back_populates="bom", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_boms_company_product_version", "company_id", "product_id", "version", unique=True),
    )


class BOMItem(Base):
    __tablename__ = "bom_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bom_id = Column(String(36), ForeignKey("boms.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_item_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    quantity = Column(Numeric(18, 6), nullable=False)
    wastage_percent = Column(Numeric(8, 4), nullable=False, default=0)
    uom_id = Column(String(36), ForeignKey("uom.id"))
    conversion_factor = Column(Numeric(18, 8), default=1)

    bom = relationship("BOM", back_populates="items")
    raw_item = relationship("Item", foreign_keys=[raw_item_id])
    uom = relationship("UOM")
