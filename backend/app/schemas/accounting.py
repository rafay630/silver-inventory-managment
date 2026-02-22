from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ── Chart of Accounts ──
class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: str  # asset, liability, equity, income, expense
    parent_id: Optional[str] = None

class AccountOut(BaseModel):
    id: str
    company_id: str
    code: str
    name: str
    account_type: str
    parent_id: Optional[str] = None
    is_system: bool
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ── Journal Entry ──
class JournalEntryLineCreate(BaseModel):
    account_id: str
    debit: float = 0
    credit: float = 0
    description: Optional[str] = None

class JournalEntryCreate(BaseModel):
    entry_date: date
    description: Optional[str] = None
    lines: List[JournalEntryLineCreate]

class JournalEntryLineOut(BaseModel):
    id: str
    account_id: str
    debit: float
    credit: float
    description: Optional[str] = None
    class Config:
        from_attributes = True

class JournalEntryOut(BaseModel):
    id: str
    company_id: str
    entry_number: str
    entry_date: date
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    is_system_generated: bool
    is_posted: bool
    created_by: Optional[str] = None
    created_at: datetime
    lines: List[JournalEntryLineOut] = []
    class Config:
        from_attributes = True


# ── Trial Balance ──
class TrialBalanceRow(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    account_type: str
    debit: float
    credit: float

class TrialBalanceReport(BaseModel):
    as_of_date: date
    rows: List[TrialBalanceRow]
    total_debit: float
    total_credit: float


# ── P&L ──
class PLRow(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    amount: float

class ProfitAndLossReport(BaseModel):
    from_date: date
    to_date: date
    income: List[PLRow]
    expenses: List[PLRow]
    total_income: float
    total_expenses: float
    net_profit: float


# ── Balance Sheet ──
class BSRow(BaseModel):
    account_id: str
    account_code: str
    account_name: str
    amount: float

class BalanceSheetReport(BaseModel):
    as_of_date: date
    assets: List[BSRow]
    liabilities: List[BSRow]
    equity: List[BSRow]
    total_assets: float
    total_liabilities: float
    total_equity: float
