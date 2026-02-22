"""
Report Service — All 8 required reports.
"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.stock_ledger import StockLedger
from app.models.item import Item
from app.models.warehouse import Warehouse
from app.models.production import ProductionOrder
from app.models.wip import WIPIssue, WIPIssueItem
from app.models.expense import ProductionExpense
from app.services.stock_ledger_service import StockLedgerService
from app.services.accounting_service import AccountingService


class ReportService:

    @staticmethod
    def stock_ledger_report(
        db: Session,
        company_id: str,
        item_id: str = None,
        warehouse_id: str = None,
        from_date: date = None,
        to_date: date = None,
    ) -> list:
        """Full stock ledger with running balance."""
        q = db.query(
            StockLedger,
            Item.name.label("item_name"),
            Item.sku.label("item_sku"),
            Warehouse.name.label("warehouse_name"),
        ).join(
            Item, StockLedger.item_id == Item.id,
        ).join(
            Warehouse, StockLedger.warehouse_id == Warehouse.id,
        ).filter(
            StockLedger.company_id == company_id,
        ).order_by(StockLedger.created_at)

        if item_id:
            q = q.filter(StockLedger.item_id == item_id)
        if warehouse_id:
            q = q.filter(StockLedger.warehouse_id == warehouse_id)
        if from_date:
            q = q.filter(StockLedger.created_at >= from_date)
        if to_date:
            q = q.filter(StockLedger.created_at <= to_date)

        results = []
        running_balance = {}
        for row in q.all():
            sl = row[0]
            key = (sl.item_id, sl.warehouse_id)
            bal = running_balance.get(key, 0)
            bal += float(sl.qty_in) - float(sl.qty_out)
            running_balance[key] = bal

            results.append({
                "id": sl.id,
                "item_id": sl.item_id,
                "item_name": row.item_name,
                "item_sku": row.item_sku,
                "warehouse_id": sl.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "qty_in": float(sl.qty_in),
                "qty_out": float(sl.qty_out),
                "unit_cost": float(sl.unit_cost),
                "reference_type": sl.reference_type,
                "reference_id": sl.reference_id,
                "running_balance": bal,
                "created_at": sl.created_at.isoformat() if sl.created_at else None,
            })
        return results

    @staticmethod
    def inventory_valuation(
        db: Session,
        company_id: str,
        warehouse_id: str = None,
    ) -> list:
        """Inventory valuation using weighted average cost."""
        return StockLedgerService.get_all_balances(
            db, company_id, warehouse_id=warehouse_id,
        )

    @staticmethod
    def production_cost_sheet(
        db: Session,
        company_id: str,
        order_id: str,
    ) -> dict:
        """Detailed cost breakdown for a production order."""
        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == order_id,
            ProductionOrder.company_id == company_id,
        ).first()
        if not order:
            return {}

        # Material costs
        material_items = db.query(
            WIPIssueItem.item_id,
            Item.name.label("item_name"),
            func.sum(WIPIssueItem.quantity).label("total_qty"),
            func.sum(WIPIssueItem.total_cost).label("total_cost"),
        ).join(
            WIPIssue, WIPIssueItem.wip_issue_id == WIPIssue.id,
        ).join(
            Item, WIPIssueItem.item_id == Item.id,
        ).filter(
            WIPIssue.production_order_id == order_id,
        ).group_by(
            WIPIssueItem.item_id, Item.name,
        ).all()

        materials = [{
            "item_id": m.item_id,
            "item_name": m.item_name,
            "quantity": float(m.total_qty),
            "cost": float(m.total_cost),
        } for m in material_items]

        total_material_cost = sum(m["cost"] for m in materials)

        # Expenses
        expenses = db.query(ProductionExpense).filter(
            ProductionExpense.production_order_id == order_id,
        ).all()

        expense_list = [{
            "id": e.id,
            "expense_type": e.expense_type,
            "description": e.description,
            "amount": float(e.amount),
            "date": e.expense_date.isoformat() if e.expense_date else None,
        } for e in expenses]

        total_expenses = sum(e["amount"] for e in expense_list)
        total_cost = total_material_cost + total_expenses
        completed = float(order.completed_qty)
        unit_cost = total_cost / completed if completed > 0 else 0

        return {
            "order_id": order.id,
            "order_number": order.order_number,
            "product_id": order.product_id,
            "order_qty": float(order.order_qty),
            "completed_qty": completed,
            "status": order.status,
            "materials": materials,
            "total_material_cost": round(total_material_cost, 4),
            "expenses": expense_list,
            "total_expenses": round(total_expenses, 4),
            "total_production_cost": round(total_cost, 4),
            "unit_cost": round(unit_cost, 4),
        }

    @staticmethod
    def wip_summary(
        db: Session,
        company_id: str,
    ) -> list:
        """WIP summary — all in-progress production orders with costs."""
        orders = db.query(ProductionOrder).filter(
            ProductionOrder.company_id == company_id,
            ProductionOrder.status == "in_progress",
        ).all()

        results = []
        for order in orders:
            material_cost = db.query(
                func.coalesce(func.sum(WIPIssueItem.total_cost), 0)
            ).join(
                WIPIssue, WIPIssueItem.wip_issue_id == WIPIssue.id
            ).filter(
                WIPIssue.production_order_id == order.id,
            ).scalar()

            expense_cost = db.query(
                func.coalesce(func.sum(ProductionExpense.amount), 0)
            ).filter(
                ProductionExpense.production_order_id == order.id,
            ).scalar()

            results.append({
                "order_id": order.id,
                "order_number": order.order_number,
                "product_id": order.product_id,
                "order_qty": float(order.order_qty),
                "completed_qty": float(order.completed_qty),
                "material_cost": float(material_cost),
                "expense_cost": float(expense_cost),
                "total_wip_value": float(material_cost) + float(expense_cost),
            })

        return results

    @staticmethod
    def material_consumption_report(
        db: Session,
        company_id: str,
        from_date: date = None,
        to_date: date = None,
    ) -> list:
        """Material consumption grouped by item."""
        q = db.query(
            WIPIssueItem.item_id,
            Item.name.label("item_name"),
            func.sum(WIPIssueItem.quantity).label("total_qty"),
            func.sum(WIPIssueItem.total_cost).label("total_cost"),
        ).join(
            WIPIssue, WIPIssueItem.wip_issue_id == WIPIssue.id,
        ).join(
            Item, WIPIssueItem.item_id == Item.id,
        ).filter(
            WIPIssue.company_id == company_id,
        )

        if from_date:
            q = q.filter(WIPIssue.issue_date >= from_date)
        if to_date:
            q = q.filter(WIPIssue.issue_date <= to_date)

        q = q.group_by(WIPIssueItem.item_id, Item.name).order_by(Item.name)

        return [{
            "item_id": row.item_id,
            "item_name": row.item_name,
            "total_quantity": float(row.total_qty),
            "total_cost": float(row.total_cost),
        } for row in q.all()]

    @staticmethod
    def trial_balance(db: Session, company_id: str, as_of_date: date = None) -> dict:
        return AccountingService.get_trial_balance(db, company_id, as_of_date)

    @staticmethod
    def profit_and_loss(db: Session, company_id: str, from_date: date, to_date: date) -> dict:
        return AccountingService.get_profit_and_loss(db, company_id, from_date, to_date)

    @staticmethod
    def balance_sheet(db: Session, company_id: str, as_of_date: date = None) -> dict:
        return AccountingService.get_balance_sheet(db, company_id, as_of_date)
