"""
WIP Service — Material issuance to production.

On WIP Issue:
1) Debit stock_ledger (qty_out) for each raw material
2) Create journal entry: Dr Work In Progress, Cr Raw Material Inventory
3) Uses weighted average cost from stock ledger
"""
import uuid
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.wip import WIPIssue, WIPIssueItem
from app.models.production import ProductionOrder
from app.services.stock_ledger_service import StockLedgerService
from app.services.accounting_service import AccountingService


class WIPService:

    @staticmethod
    def _next_issue_number(db: Session, company_id: str) -> str:
        count = db.query(func.count(WIPIssue.id)).filter(
            WIPIssue.company_id == company_id,
        ).scalar() or 0
        return f"WIP-{count + 1:06d}"

    @staticmethod
    def issue_materials(
        db: Session,
        company_id: str,
        production_order_id: str,
        issue_date: date,
        items: list[dict],
        created_by: str = None,
    ) -> WIPIssue:
        """
        Issue raw materials to production (WIP).

        For each item:
        1) Get weighted average cost
        2) Insert stock_ledger entry (qty_out)
        3) Calculate total cost

        Then create journal entry:
        Dr Work In Progress (total)
            Cr Raw Material Inventory (total)
        """
        # Validate production order
        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == production_order_id,
            ProductionOrder.company_id == company_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Production order not found")
        if order.status not in ("planned", "in_progress"):
            raise HTTPException(status_code=400, detail=f"Cannot issue materials for order in '{order.status}' status")

        # Auto-transition to in_progress
        if order.status == "planned":
            order.status = "in_progress"

        wip_issue = WIPIssue(
            id=str(uuid.uuid4()),
            company_id=company_id,
            production_order_id=production_order_id,
            issue_number=WIPService._next_issue_number(db, company_id),
            issue_date=issue_date,
            created_by=created_by,
        )
        db.add(wip_issue)
        db.flush()

        total_cost = 0.0

        for item_data in items:
            item_id = item_data["item_id"]
            warehouse_id = item_data["warehouse_id"]
            quantity = float(item_data["quantity"])

            # Get weighted average cost
            unit_cost = StockLedgerService.get_weighted_average_cost(
                db, company_id, item_id, warehouse_id,
            )

            item_total = round(quantity * unit_cost, 4)
            total_cost += item_total

            # Record stock_ledger entry (qty_out)
            StockLedgerService.record_entry(
                db=db,
                company_id=company_id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                qty_in=0,
                qty_out=quantity,
                unit_cost=unit_cost,
                reference_type="wip_issue",
                reference_id=wip_issue.id,
                description=f"WIP Issue {wip_issue.issue_number} for PO {order.order_number}",
            )

            # Create WIP issue item
            wip_item = WIPIssueItem(
                id=str(uuid.uuid4()),
                wip_issue_id=wip_issue.id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                unit_cost=unit_cost,
                total_cost=item_total,
            )
            db.add(wip_item)

        # Create journal entry: Dr WIP, Cr Raw Material Inventory
        wip_account = AccountingService.get_account_by_code(db, company_id, "1200")  # WIP
        rm_account = AccountingService.get_account_by_code(db, company_id, "1100")  # Raw Material

        je = AccountingService.create_journal_entry(
            db=db,
            company_id=company_id,
            entry_date=issue_date,
            lines=[
                {"account_id": wip_account.id, "debit": total_cost, "credit": 0, "description": "WIP material issue"},
                {"account_id": rm_account.id, "debit": 0, "credit": total_cost, "description": "Raw material consumed"},
            ],
            reference_type="wip_issue",
            reference_id=wip_issue.id,
            description=f"Material issue for PO {order.order_number}",
            created_by=created_by,
        )

        wip_issue.journal_entry_id = je.id
        db.flush()
        return wip_issue
