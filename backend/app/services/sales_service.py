"""
Sales Service — Sell finished goods.

On sale:
1) Record stock_ledger (qty_out) for each item
2) Journal: Dr COGS, Cr Finished Goods Inventory (at weighted avg cost)
3) Journal: Dr Accounts Receivable, Cr Sales Revenue (at selling price)
"""
import uuid
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.sales import SalesOrder, SalesOrderItem
from app.models.item import Item
from app.services.stock_ledger_service import StockLedgerService
from app.services.accounting_service import AccountingService


class SalesService:

    @staticmethod
    def _next_order_number(db: Session, company_id: str) -> str:
        count = db.query(func.count(SalesOrder.id)).filter(
            SalesOrder.company_id == company_id,
        ).scalar() or 0
        return f"SO-{count + 1:06d}"

    @staticmethod
    def create_sale(
        db: Session,
        company_id: str,
        customer_name: str,
        order_date: date,
        items: list[dict],
        notes: str = "",
        created_by: str = None,
    ) -> SalesOrder:
        """
        Create a sales order and process inventory + accounting.
        """
        order = SalesOrder(
            id=str(uuid.uuid4()),
            company_id=company_id,
            order_number=SalesService._next_order_number(db, company_id),
            customer_name=customer_name,
            order_date=order_date,
            status="completed",
            notes=notes,
            created_by=created_by,
        )
        db.add(order)
        db.flush()

        total_revenue = 0.0
        total_cogs = 0.0

        for item_data in items:
            item_id = item_data["item_id"]
            warehouse_id = item_data["warehouse_id"]
            quantity = float(item_data["quantity"])
            unit_price = float(item_data["unit_price"])

            # Validate finished good
            item = db.query(Item).filter(
                Item.id == item_id,
                Item.company_id == company_id,
            ).first()
            if not item:
                raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")

            # Get weighted average cost
            unit_cost = StockLedgerService.get_weighted_average_cost(
                db, company_id, item_id, warehouse_id,
            )

            line_revenue = round(quantity * unit_price, 4)
            line_cost = round(quantity * unit_cost, 4)
            total_revenue += line_revenue
            total_cogs += line_cost

            # Record stock_ledger entry (qty_out)
            StockLedgerService.record_entry(
                db=db,
                company_id=company_id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                qty_in=0,
                qty_out=quantity,
                unit_cost=unit_cost,
                reference_type="sale",
                reference_id=order.id,
                description=f"Sale {order.order_number} to {customer_name}",
            )

            order_item = SalesOrderItem(
                id=str(uuid.uuid4()),
                sales_order_id=order.id,
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                unit_price=unit_price,
                unit_cost=unit_cost,
                total_price=line_revenue,
            )
            db.add(order_item)

        order.total_amount = total_revenue
        order.total_cost = total_cogs

        # Journal entries
        cogs_account = AccountingService.get_account_by_code(db, company_id, "5100")  # COGS
        fg_account = AccountingService.get_account_by_code(db, company_id, "1300")  # Finished Goods
        ar_account = AccountingService.get_account_by_code(db, company_id, "1500")  # Accounts Receivable
        revenue_account = AccountingService.get_account_by_code(db, company_id, "4100")  # Sales Revenue

        je = AccountingService.create_journal_entry(
            db=db,
            company_id=company_id,
            entry_date=order_date,
            lines=[
                # COGS entry
                {"account_id": cogs_account.id, "debit": total_cogs, "credit": 0,
                 "description": "Cost of goods sold"},
                {"account_id": fg_account.id, "debit": 0, "credit": total_cogs,
                 "description": "Finished goods inventory reduced"},
                # Revenue entry
                {"account_id": ar_account.id, "debit": total_revenue, "credit": 0,
                 "description": "Accounts receivable"},
                {"account_id": revenue_account.id, "debit": 0, "credit": total_revenue,
                 "description": "Sales revenue"},
            ],
            reference_type="sale",
            reference_id=order.id,
            description=f"Sale {order.order_number} to {customer_name}",
            created_by=created_by,
        )

        order.journal_entry_id = je.id
        db.flush()
        return order
