"""
Accounting Engine — Double-entry bookkeeping.

Every journal entry MUST balance: total_debit == total_credit.
System-generated entries cannot be manually edited.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.accounting import ChartOfAccounts, JournalEntry, JournalEntryLine


# ── Default Chart of Accounts codes (System Accounts) ──
SYSTEM_ACCOUNTS = {
    # Assets
    "1100": ("Raw Material Inventory", "asset"),
    "1200": ("Work In Progress", "asset"),
    "1300": ("Finished Goods Inventory", "asset"),
    "1400": ("Machinery", "asset"),
    "1410": ("Accumulated Depreciation", "asset"),
    "1500": ("Accounts Receivable", "asset"),
    "1600": ("Cash", "asset"),
    # Liabilities
    "2100": ("Accounts Payable", "liability"),
    "2200": ("Salary Payable", "liability"),
    # Equity
    "3100": ("Retained Earnings", "equity"),
    # Income
    "4100": ("Sales Revenue", "income"),
    # Expenses
    "5100": ("Cost of Goods Sold", "expense"),
    "5200": ("Direct Labor", "expense"),
    "5300": ("Indirect Labor", "expense"),
    "5400": ("Electricity", "expense"),
    "5500": ("Factory Rent", "expense"),
    "5600": ("Machine Depreciation Expense", "expense"),
    "5700": ("Lubricants", "expense"),
    "5800": ("Job Work Expense", "expense"),
}

# Map expense types to account codes for absorption costing
EXPENSE_TYPE_ACCOUNT_MAP = {
    "direct_labor": "5200",
    "indirect_labor": "5300",
    "electricity": "5400",
    "factory_rent": "5500",
    "machine_depreciation": "5600",
    "lubricants": "5700",
    "job_work": "5800",
}


class AccountingService:

    @staticmethod
    def seed_chart_of_accounts(db: Session, company_id: str):
        """Create default system accounts for a new company."""
        for code, (name, acc_type) in SYSTEM_ACCOUNTS.items():
            exists = db.query(ChartOfAccounts).filter(
                ChartOfAccounts.company_id == company_id,
                ChartOfAccounts.code == code,
            ).first()
            if not exists:
                account = ChartOfAccounts(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    code=code,
                    name=name,
                    account_type=acc_type,
                    is_system=True,
                )
                db.add(account)
        db.flush()

    @staticmethod
    def get_account_by_code(db: Session, company_id: str, code: str) -> ChartOfAccounts:
        """Get account by its code within a company."""
        account = db.query(ChartOfAccounts).filter(
            ChartOfAccounts.company_id == company_id,
            ChartOfAccounts.code == code,
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account with code '{code}' not found. Run seed to create system accounts.",
            )
        return account

    @staticmethod
    def _next_entry_number(db: Session, company_id: str) -> str:
        """Generate next sequential journal entry number."""
        count = db.query(func.count(JournalEntry.id)).filter(
            JournalEntry.company_id == company_id,
        ).scalar() or 0
        return f"JE-{count + 1:06d}"

    @staticmethod
    def create_journal_entry(
        db: Session,
        company_id: str,
        entry_date: date,
        lines: list[dict],
        reference_type: str = None,
        reference_id: str = None,
        description: str = "",
        is_system_generated: bool = True,
        created_by: str = None,
    ) -> JournalEntry:
        """
        Create a balanced journal entry with lines.

        lines: list of dicts with keys: account_id, debit, credit, description
        Raises if total_debit != total_credit.
        """
        total_debit = sum(Decimal(str(line.get("debit", 0))) for line in lines)
        total_credit = sum(Decimal(str(line.get("credit", 0))) for line in lines)

        if total_debit != total_credit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Journal entry not balanced. Debit: {total_debit}, Credit: {total_credit}",
            )

        if total_debit == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Journal entry cannot have zero total.",
            )

        entry = JournalEntry(
            id=str(uuid.uuid4()),
            company_id=company_id,
            entry_number=AccountingService._next_entry_number(db, company_id),
            entry_date=entry_date,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            is_system_generated=is_system_generated,
            created_by=created_by,
        )
        db.add(entry)
        db.flush()

        for line in lines:
            je_line = JournalEntryLine(
                id=str(uuid.uuid4()),
                journal_entry_id=entry.id,
                account_id=line["account_id"],
                debit=line.get("debit", 0),
                credit=line.get("credit", 0),
                description=line.get("description", ""),
            )
            db.add(je_line)

        db.flush()
        return entry

    @staticmethod
    def get_trial_balance(
        db: Session,
        company_id: str,
        as_of_date: date = None,
    ) -> dict:
        """
        Trial Balance: aggregate all debits/credits per account.
        """
        q = db.query(
            JournalEntryLine.account_id,
            ChartOfAccounts.code,
            ChartOfAccounts.name,
            ChartOfAccounts.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        ).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id,
        ).join(
            ChartOfAccounts, JournalEntryLine.account_id == ChartOfAccounts.id,
        ).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True,
        )

        if as_of_date:
            q = q.filter(JournalEntry.entry_date <= as_of_date)

        q = q.group_by(
            JournalEntryLine.account_id,
            ChartOfAccounts.code,
            ChartOfAccounts.name,
            ChartOfAccounts.account_type,
        ).order_by(ChartOfAccounts.code)

        rows = []
        total_debit = 0
        total_credit = 0
        for row in q.all():
            d = float(row.total_debit)
            c = float(row.total_credit)
            total_debit += d
            total_credit += c
            rows.append({
                "account_id": row.account_id,
                "account_code": row.code,
                "account_name": row.name,
                "account_type": row.account_type,
                "debit": d,
                "credit": c,
            })

        return {
            "as_of_date": as_of_date or date.today(),
            "rows": rows,
            "total_debit": round(total_debit, 4),
            "total_credit": round(total_credit, 4),
            "is_balanced": abs(total_debit - total_credit) < 0.01,
        }

    @staticmethod
    def get_profit_and_loss(
        db: Session,
        company_id: str,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Profit & Loss: Income - Expenses for a period."""
        q = db.query(
            JournalEntryLine.account_id,
            ChartOfAccounts.code,
            ChartOfAccounts.name,
            ChartOfAccounts.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        ).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id,
        ).join(
            ChartOfAccounts, JournalEntryLine.account_id == ChartOfAccounts.id,
        ).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True,
            JournalEntry.entry_date >= from_date,
            JournalEntry.entry_date <= to_date,
            ChartOfAccounts.account_type.in_(["income", "expense"]),
        ).group_by(
            JournalEntryLine.account_id,
            ChartOfAccounts.code,
            ChartOfAccounts.name,
            ChartOfAccounts.account_type,
        ).order_by(ChartOfAccounts.code)

        income = []
        expenses = []
        total_income = 0
        total_expenses = 0

        for row in q.all():
            d = float(row.total_debit)
            c = float(row.total_credit)

            if row.account_type == "income":
                amount = c - d  # Income normal balance is credit
                total_income += amount
                income.append({
                    "account_id": row.account_id,
                    "account_code": row.code,
                    "account_name": row.name,
                    "amount": amount,
                })
            else:
                amount = d - c  # Expense normal balance is debit
                total_expenses += amount
                expenses.append({
                    "account_id": row.account_id,
                    "account_code": row.code,
                    "account_name": row.name,
                    "amount": amount,
                })

        return {
            "from_date": from_date,
            "to_date": to_date,
            "income": income,
            "expenses": expenses,
            "total_income": round(total_income, 4),
            "total_expenses": round(total_expenses, 4),
            "net_profit": round(total_income - total_expenses, 4),
        }

    @staticmethod
    def get_balance_sheet(
        db: Session,
        company_id: str,
        as_of_date: date = None,
    ) -> dict:
        """Balance Sheet: Assets = Liabilities + Equity as of a date."""
        q = db.query(
            JournalEntryLine.account_id,
            ChartOfAccounts.code,
            ChartOfAccounts.name,
            ChartOfAccounts.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        ).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id,
        ).join(
            ChartOfAccounts, JournalEntryLine.account_id == ChartOfAccounts.id,
        ).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True,
            ChartOfAccounts.account_type.in_(["asset", "liability", "equity"]),
        )

        if as_of_date:
            q = q.filter(JournalEntry.entry_date <= as_of_date)

        q = q.group_by(
            JournalEntryLine.account_id,
            ChartOfAccounts.code,
            ChartOfAccounts.name,
            ChartOfAccounts.account_type,
        ).order_by(ChartOfAccounts.code)

        assets = []
        liabilities = []
        equity = []
        total_assets = 0
        total_liabilities = 0
        total_equity = 0

        for row in q.all():
            d = float(row.total_debit)
            c = float(row.total_credit)

            if row.account_type == "asset":
                amount = d - c
                total_assets += amount
                assets.append({
                    "account_id": row.account_id,
                    "account_code": row.code,
                    "account_name": row.name,
                    "balance": amount,
                })
            elif row.account_type == "liability":
                amount = c - d
                total_liabilities += amount
                liabilities.append({
                    "account_id": row.account_id,
                    "account_code": row.code,
                    "account_name": row.name,
                    "balance": amount,
                })
            else:  # equity
                amount = c - d
                total_equity += amount
                equity.append({
                    "account_id": row.account_id,
                    "account_code": row.code,
                    "account_name": row.name,
                    "balance": amount,
                })

        # ── Compute Net Profit (Income − Expenses) and add to Equity ──
        pnl_q = db.query(
            ChartOfAccounts.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        ).join(
            JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id,
        ).join(
            ChartOfAccounts, JournalEntryLine.account_id == ChartOfAccounts.id,
        ).filter(
            JournalEntry.company_id == company_id,
            JournalEntry.is_posted == True,
            ChartOfAccounts.account_type.in_(["income", "expense"]),
        )
        if as_of_date:
            pnl_q = pnl_q.filter(JournalEntry.entry_date <= as_of_date)
        pnl_q = pnl_q.group_by(ChartOfAccounts.account_type)

        total_income = 0
        total_expenses = 0
        for row in pnl_q.all():
            d = float(row.total_debit)
            c = float(row.total_credit)
            if row.account_type == "income":
                total_income = c - d
            elif row.account_type == "expense":
                total_expenses = d - c

        net_profit = total_income - total_expenses
        if abs(net_profit) > 0.001:
            equity.append({
                "account_id": None,
                "account_code": "—",
                "account_name": "Retained Earnings (Current Period)",
                "balance": net_profit,
            })
            total_equity += net_profit

        return {
            "as_of_date": as_of_date or date.today(),
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity,
            "total_assets": round(total_assets, 4),
            "total_liabilities": round(total_liabilities, 4),
            "total_equity": round(total_equity, 4),
        }

