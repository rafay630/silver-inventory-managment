import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    order_number = Column(String(50), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    order_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default="completed", index=True)
    # Status: draft, completed, cancelled
    total_amount = Column(Numeric(18, 4), default=0)
    total_cost = Column(Numeric(18, 4), default=0)
    notes = Column(Text)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), index=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company")
    journal_entry = relationship("JournalEntry")
    creator = relationship("User")
    items = relationship("SalesOrderItem", back_populates="sales_order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sales_company_number", "company_id", "order_number", unique=True),
    )


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sales_order_id = Column(String(36), ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    total_price = Column(Numeric(18, 4), nullable=False)

    sales_order = relationship("SalesOrder", back_populates="items")
    item = relationship("Item")
    warehouse = relationship("Warehouse")
