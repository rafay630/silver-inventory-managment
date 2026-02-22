import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class StockLedger(Base):
    """
    Immutable, append-only stock ledger.
    EVERY inventory movement MUST insert a row here.
    No direct stock updates anywhere else.
    Current stock = SUM(qty_in) - SUM(qty_out) grouped by item_id + warehouse_id.
    """
    __tablename__ = "stock_ledger"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    qty_in = Column(Numeric(18, 4), nullable=False, default=0)
    qty_out = Column(Numeric(18, 4), nullable=False, default=0)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    reference_type = Column(String(50), nullable=False, index=True)
    # reference_types: purchase, wip_issue, production_completion, sale, adjustment
    reference_id = Column(String(36), nullable=False, index=True)
    description = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    item = relationship("Item")
    warehouse = relationship("Warehouse")

    __table_args__ = (
        Index("ix_stock_ledger_company_item_wh", "company_id", "item_id", "warehouse_id"),
        Index("ix_stock_ledger_ref", "reference_type", "reference_id"),
    )
