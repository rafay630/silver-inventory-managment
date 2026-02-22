import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Date, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WIPIssue(Base):
    """Header for material issuance to production."""
    __tablename__ = "wip_issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    production_order_id = Column(String(36), ForeignKey("production_orders.id"), nullable=False, index=True)
    issue_number = Column(String(50), nullable=False, index=True)
    issue_date = Column(Date, nullable=False)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), index=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    production_order = relationship("ProductionOrder")
    creator = relationship("User")
    items = relationship("WIPIssueItem", back_populates="wip_issue", cascade="all, delete-orphan")
    journal_entry = relationship("JournalEntry")

    __table_args__ = (
        Index("ix_wip_issues_company_number", "company_id", "issue_number", unique=True),
    )


class WIPIssueItem(Base):
    __tablename__ = "wip_issue_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    wip_issue_id = Column(String(36), ForeignKey("wip_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False, index=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    total_cost = Column(Numeric(18, 4), nullable=False)

    wip_issue = relationship("WIPIssue", back_populates="items")
    item = relationship("Item")
    warehouse = relationship("Warehouse")
