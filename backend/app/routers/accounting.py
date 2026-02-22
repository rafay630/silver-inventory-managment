"""Accounting Router — Chart of Accounts, Journal Entries, Financial Reports."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.accounting import ChartOfAccounts, JournalEntry
from app.models.user import User
from app.dependencies import get_current_user, require_roles
from app.schemas.accounting import (
    AccountCreate, AccountOut,
    JournalEntryCreate, JournalEntryOut,
)
from app.services.accounting_service import AccountingService
from typing import List, Optional
from datetime import date

router = APIRouter(prefix="/api/accounting", tags=["Accounting"])


# ═══ Chart of Accounts ═══
@router.post("/accounts", response_model=AccountOut, status_code=201)
def create_account(
    data: AccountCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["admin", "accountant"])),
):
    valid_types = ["asset", "liability", "equity", "income", "expense"]
    if data.account_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid account type. Valid: {', '.join(valid_types)}")

    account = ChartOfAccounts(
        id=str(uuid.uuid4()),
        company_id=user.company_id,
        code=data.code,
        name=data.name,
        account_type=data.account_type,
        parent_id=data.parent_id,
        is_system=False,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts", response_model=List[AccountOut])
def list_accounts(
    account_type: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ChartOfAccounts).filter(ChartOfAccounts.company_id == user.company_id)
    if account_type:
        q = q.filter(ChartOfAccounts.account_type == account_type)
    return q.order_by(ChartOfAccounts.code).all()


# ═══ Journal Entries ═══
@router.post("/journal-entries", response_model=JournalEntryOut, status_code=201)
def create_manual_journal(
    data: JournalEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["admin", "accountant"])),
):
    """Create a manual journal entry (non-system-generated)."""
    lines = [line.model_dump() for line in data.lines]
    je = AccountingService.create_journal_entry(
        db=db,
        company_id=user.company_id,
        entry_date=data.entry_date,
        lines=lines,
        description=data.description,
        is_system_generated=False,
        created_by=user.id,
    )
    db.commit()
    db.refresh(je)
    return je


@router.get("/journal-entries", response_model=List[JournalEntryOut])
def list_journal_entries(
    reference_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(JournalEntry).filter(JournalEntry.company_id == user.company_id)
    if reference_type:
        q = q.filter(JournalEntry.reference_type == reference_type)
    if from_date:
        q = q.filter(JournalEntry.entry_date >= from_date)
    if to_date:
        q = q.filter(JournalEntry.entry_date <= to_date)
    return q.order_by(JournalEntry.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/journal-entries/{entry_id}", response_model=JournalEntryOut)
def get_journal_entry(entry_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    je = db.query(JournalEntry).filter(
        JournalEntry.id == entry_id,
        JournalEntry.company_id == user.company_id,
    ).first()
    if not je:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return je


# ═══ Financial Reports ═══
@router.get("/trial-balance")
def trial_balance(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AccountingService.get_trial_balance(db, user.company_id, as_of_date)


@router.get("/profit-and-loss")
def profit_and_loss(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AccountingService.get_profit_and_loss(db, user.company_id, from_date, to_date)


@router.get("/balance-sheet")
def balance_sheet(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return AccountingService.get_balance_sheet(db, user.company_id, as_of_date)
