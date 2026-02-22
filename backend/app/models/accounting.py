import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ChartOfAccounts(Base):
    __tablename__ = "chart_of_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    account_type = Column(String(30), nullable=False, index=True)
    # account_type: asset, liability, equity, income, expense
    parent_id = Column(String(36), ForeignKey("chart_of_accounts.id"), index=True)
    is_system = Column(Boolean, default=False)
    # System accounts cannot be deleted or renamed
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    company = relationship("Company")
    parent = relationship("ChartOfAccounts", remote_side=[id])

    __table_args__ = (
        Index("ix_coa_company_code", "company_id", "code", unique=True),
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    entry_number = Column(String(50), nullable=False, index=True)
    entry_date = Column(Date, nullable=False)
    reference_type = Column(String(50), index=True)
    # reference_types: wip_issue, production_expense, production_completion, sale
    reference_id = Column(String(36), index=True)
    description = Column(Text)
    is_system_generated = Column(Boolean, default=False)
    is_posted = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    creator = relationship("User")
    lines = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_je_company_number", "company_id", "entry_number", unique=True),
        Index("ix_je_ref", "reference_type", "reference_id"),
    )


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("chart_of_accounts.id"), nullable=False, index=True)
    debit = Column(Numeric(18, 4), nullable=False, default=0)
    credit = Column(Numeric(18, 4), nullable=False, default=0)
    description = Column(String(500))

    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccounts")
