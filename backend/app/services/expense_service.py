"""
Expense Service — Record production expenses with absorption costing.

On saving expense:
Dr Work In Progress
    Cr Expense Account (mapped by expense type)
"""
import uuid
from datetime import date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.expense import ProductionExpense
from app.models.production import ProductionOrder
from app.services.accounting_service import AccountingService, EXPENSE_TYPE_ACCOUNT_MAP


VALID_EXPENSE_TYPES = [
    "direct_labor", "job_work", "factory_rent", "electricity",
    "machine_depreciation", "indirect_labor", "lubricants",
]


class ExpenseService:

    @staticmethod
    def record_expense(
        db: Session,
        company_id: str,
        production_order_id: str,
        expense_type: str,
        amount: float,
        expense_date: date,
        description: str = "",
        created_by: str = None,
    ) -> ProductionExpense:
        """
        Record a production expense and create absorption costing journal entry.
        Dr Work In Progress
            Cr Expense Account
        """
        # Validate expense type
        if expense_type not in VALID_EXPENSE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid expense type. Valid types: {', '.join(VALID_EXPENSE_TYPES)}",
            )

        # Validate production order
        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == production_order_id,
            ProductionOrder.company_id == company_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Production order not found")
        if order.status not in ("planned", "in_progress"):
            raise HTTPException(status_code=400, detail=f"Cannot add expenses to order in '{order.status}' status")

        expense = ProductionExpense(
            id=str(uuid.uuid4()),
            company_id=company_id,
            production_order_id=production_order_id,
            expense_type=expense_type,
            description=description,
            amount=amount,
            expense_date=expense_date,
            created_by=created_by,
        )
        db.add(expense)
        db.flush()

        # Absorption costing: Dr WIP, Cr Expense Account
        wip_account = AccountingService.get_account_by_code(db, company_id, "1200")
        expense_code = EXPENSE_TYPE_ACCOUNT_MAP.get(expense_type)
        expense_account = AccountingService.get_account_by_code(db, company_id, expense_code)

        je = AccountingService.create_journal_entry(
            db=db,
            company_id=company_id,
            entry_date=expense_date,
            lines=[
                {"account_id": wip_account.id, "debit": amount, "credit": 0,
                 "description": f"WIP - {expense_type}"},
                {"account_id": expense_account.id, "debit": 0, "credit": amount,
                 "description": f"Expense absorbed - {expense_type}"},
            ],
            reference_type="production_expense",
            reference_id=expense.id,
            description=f"Production expense ({expense_type}) for PO {order.order_number}",
            created_by=created_by,
        )

        expense.journal_entry_id = je.id
        db.flush()
        return expense
