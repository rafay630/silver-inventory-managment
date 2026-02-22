import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductionExpense(Base):
    __tablename__ = "production_expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    production_order_id = Column(String(36), ForeignKey("production_orders.id"), nullable=False, index=True)
    expense_type = Column(String(50), nullable=False, index=True)
    # expense_types: direct_labor, job_work, factory_rent, electricity,
    #                machine_depreciation, indirect_labor, lubricants
    description = Column(Text)
    amount = Column(Numeric(18, 4), nullable=False)
    expense_date = Column(Date, nullable=False)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id"), index=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    production_order = relationship("ProductionOrder")
    journal_entry = relationship("JournalEntry")
    creator = relationship("User")

    __table_args__ = (
        Index("ix_prod_expenses_company_order", "company_id", "production_order_id"),
    )
