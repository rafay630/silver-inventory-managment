"""
Production Completion Service — Finalize production, calculate costs, create finished goods.

On completion:
1) total_material_cost = sum(wip_issue_items.total_cost)
2) total_expenses = sum(production_expenses.amount)
3) unit_cost = total_production_cost / completed_qty
4) Insert stock_ledger (qty_in = completed_qty, unit_cost)
5) Journal: Dr Finished Goods Inventory, Cr Work In Progress
6) After full completion: WIP balance must become zero
"""
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.production import ProductionOrder
from app.models.wip import WIPIssue, WIPIssueItem
from app.models.expense import ProductionExpense
from app.services.stock_ledger_service import StockLedgerService
from app.services.accounting_service import AccountingService


class CompletionService:

    @staticmethod
    def complete_production(
        db: Session,
        company_id: str,
        order_id: str,
        completed_qty: float,
        completion_date: date,
        created_by: str = None,
    ) -> dict:
        """
        Complete a production order (full or partial).
        """
        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == order_id,
            ProductionOrder.company_id == company_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Production order not found")
        if order.status not in ("in_progress",):
            raise HTTPException(status_code=400, detail=f"Cannot complete order in '{order.status}' status")

        remaining = float(order.order_qty) - float(order.completed_qty)
        if completed_qty > remaining:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot complete {completed_qty} units. Remaining: {remaining}",
            )

        # Calculate total material cost from all WIP issues
        total_material_cost = db.query(
            func.coalesce(func.sum(WIPIssueItem.total_cost), 0)
        ).join(
            WIPIssue, WIPIssueItem.wip_issue_id == WIPIssue.id
        ).filter(
            WIPIssue.production_order_id == order_id,
        ).scalar()
        total_material_cost = float(total_material_cost)

        # Calculate total expenses
        total_expenses = db.query(
            func.coalesce(func.sum(ProductionExpense.amount), 0)
        ).filter(
            ProductionExpense.production_order_id == order_id,
        ).scalar()
        total_expenses = float(total_expenses)

        total_production_cost = total_material_cost + total_expenses
        total_completed_so_far = float(order.completed_qty) + completed_qty

        # Unit cost based on TOTAL order completed qty (proportional)
        unit_cost = total_production_cost / total_completed_so_far if total_completed_so_far > 0 else 0

        # Insert stock_ledger (finished goods in)
        StockLedgerService.record_entry(
            db=db,
            company_id=company_id,
            item_id=order.product_id,
            warehouse_id=order.warehouse_id,
            qty_in=completed_qty,
            qty_out=0,
            unit_cost=round(unit_cost, 4),
            reference_type="production_completion",
            reference_id=order.id,
            description=f"Production completion for PO {order.order_number}",
        )

        # Journal: Dr Finished Goods, Cr WIP
        cost_for_this_completion = round(completed_qty * unit_cost, 4)
        fg_account = AccountingService.get_account_by_code(db, company_id, "1300")
        wip_account = AccountingService.get_account_by_code(db, company_id, "1200")

        je = AccountingService.create_journal_entry(
            db=db,
            company_id=company_id,
            entry_date=completion_date,
            lines=[
                {"account_id": fg_account.id, "debit": cost_for_this_completion, "credit": 0,
                 "description": "Finished goods received from production"},
                {"account_id": wip_account.id, "debit": 0, "credit": cost_for_this_completion,
                 "description": "WIP cleared on production completion"},
            ],
            reference_type="production_completion",
            reference_id=order.id,
            description=f"Production completion for PO {order.order_number}",
            created_by=created_by,
        )

        # Update order
        order.completed_qty = total_completed_so_far
        if total_completed_so_far >= float(order.order_qty):
            order.status = "completed"
            order.end_date = completion_date

        db.flush()

        return {
            "production_order_id": order.id,
            "order_number": order.order_number,
            "completed_qty": completed_qty,
            "total_completed": total_completed_so_far,
            "total_material_cost": total_material_cost,
            "total_expenses": total_expenses,
            "total_production_cost": total_production_cost,
            "unit_cost": round(unit_cost, 4),
            "journal_entry_id": je.id,
            "status": order.status,
        }
