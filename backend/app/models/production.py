import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductionOrder(Base):
    __tablename__ = "production_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    bom_id = Column(String(36), ForeignKey("boms.id"), nullable=False, index=True)
    order_qty = Column(Numeric(18, 4), nullable=False)
    completed_qty = Column(Numeric(18, 4), default=0)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="planned", index=True)
    # Status: planned, in_progress, completed, cancelled
    start_date = Column(Date)
    end_date = Column(Date)
    notes = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company")
    product = relationship("Item", foreign_keys=[product_id])
    bom = relationship("BOM")
    warehouse = relationship("Warehouse")
    creator = relationship("User")
    requirements = relationship("ProductionRequirement", back_populates="production_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_prod_orders_company_number", "company_id", "order_number", unique=True),
    )


class ProductionRequirement(Base):
    """Snapshot of material requirements calculated at order creation."""
    __tablename__ = "production_requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    production_order_id = Column(String(36), ForeignKey("production_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    required_qty = Column(Numeric(18, 4), nullable=False)
    available_qty = Column(Numeric(18, 4), nullable=False, default=0)
    status = Column(String(30), nullable=False, default="adequate")
    # Status: adequate, insufficient

    production_order = relationship("ProductionOrder", back_populates="requirements")
    item = relationship("Item")
