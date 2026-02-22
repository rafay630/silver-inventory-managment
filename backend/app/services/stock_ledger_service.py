"""
Stock Ledger Service — The backbone of inventory management.

All inventory movements MUST go through this service.
Stock balance = SUM(qty_in) - SUM(qty_out) per (item, warehouse).
Cost is tracked using Weighted Average method.
"""
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.stock_ledger import StockLedger
from app.models.item import Item
from app.models.warehouse import Warehouse
from app.config import get_settings

settings = get_settings()


class StockLedgerService:

    @staticmethod
    def record_entry(
        db: Session,
        company_id: str,
        item_id: str,
        warehouse_id: str,
        qty_in: float,
        qty_out: float,
        unit_cost: float,
        reference_type: str,
        reference_id: str,
        description: str = "",
    ) -> StockLedger:
        """
        Insert an immutable stock ledger entry. Validates stock availability
        when PREVENT_NEGATIVE_STOCK is enabled.
        """
        if qty_out > 0 and settings.PREVENT_NEGATIVE_STOCK:
            balance = StockLedgerService.get_stock_balance(db, company_id, item_id, warehouse_id)
            if balance < qty_out:
                item = db.query(Item).filter(Item.id == item_id).first()
                item_name = item.name if item else item_id
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{item_name}'. Available: {balance}, Requested: {qty_out}",
                )

        entry = StockLedger(
            id=str(uuid.uuid4()),
            company_id=company_id,
            item_id=item_id,
            warehouse_id=warehouse_id,
            qty_in=qty_in,
            qty_out=qty_out,
            unit_cost=unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
        )
        db.add(entry)
        return entry

    @staticmethod
    def get_stock_balance(
        db: Session,
        company_id: str,
        item_id: str,
        warehouse_id: str | None = None,
    ) -> float:
        """Current stock = SUM(qty_in) - SUM(qty_out)."""
        q = db.query(
            func.coalesce(func.sum(StockLedger.qty_in), 0) -
            func.coalesce(func.sum(StockLedger.qty_out), 0)
        ).filter(
            StockLedger.company_id == company_id,
            StockLedger.item_id == item_id,
        )
        if warehouse_id:
            q = q.filter(StockLedger.warehouse_id == warehouse_id)
        balance = q.scalar() or 0
        return float(balance)

    @staticmethod
    def get_weighted_average_cost(
        db: Session,
        company_id: str,
        item_id: str,
        warehouse_id: str | None = None,
    ) -> float:
        """
        Weighted Average Cost = SUM(qty_in × unit_cost) / SUM(qty_in)
        Only considers inbound entries (qty_in > 0).
        """
        q = db.query(
            func.sum(StockLedger.qty_in * StockLedger.unit_cost),
            func.sum(StockLedger.qty_in),
        ).filter(
            StockLedger.company_id == company_id,
            StockLedger.item_id == item_id,
            StockLedger.qty_in > 0,
        )
        if warehouse_id:
            q = q.filter(StockLedger.warehouse_id == warehouse_id)

        total_cost, total_qty = q.first()
        if not total_qty or float(total_qty) == 0:
            # Fall back to item base cost
            item = db.query(Item).filter(Item.id == item_id).first()
            return float(item.base_cost) if item and item.base_cost else 0.0
        return float(total_cost) / float(total_qty)

    @staticmethod
    def get_all_balances(
        db: Session,
        company_id: str,
        item_type: str | None = None,
        warehouse_id: str | None = None,
    ) -> list:
        """Get stock balance for all items with optional filters."""
        q = db.query(
            StockLedger.item_id,
            Item.name.label("item_name"),
            StockLedger.warehouse_id,
            Warehouse.name.label("warehouse_name"),
            (func.coalesce(func.sum(StockLedger.qty_in), 0) -
             func.coalesce(func.sum(StockLedger.qty_out), 0)).label("balance"),
        ).join(
            Item, StockLedger.item_id == Item.id
        ).join(
            Warehouse, StockLedger.warehouse_id == Warehouse.id
        ).filter(
            StockLedger.company_id == company_id,
        ).group_by(
            StockLedger.item_id, Item.name,
            StockLedger.warehouse_id, Warehouse.name,
        )

        if item_type:
            q = q.filter(Item.item_type == item_type)
        if warehouse_id:
            q = q.filter(StockLedger.warehouse_id == warehouse_id)

        results = []
        for row in q.all():
            balance = float(row.balance)
            wac = StockLedgerService.get_weighted_average_cost(
                db, company_id, row.item_id, row.warehouse_id,
            )
            results.append({
                "item_id": row.item_id,
                "item_name": row.item_name,
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "balance": balance,
                "weighted_avg_cost": wac,
                "total_value": round(balance * wac, 4),
            })
        return results

    @staticmethod
    def get_ledger_entries(
        db: Session,
        company_id: str,
        item_id: str | None = None,
        warehouse_id: str | None = None,
        reference_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """Get stock ledger entries with filters."""
        q = db.query(StockLedger).filter(
            StockLedger.company_id == company_id,
        ).order_by(StockLedger.created_at.desc())

        if item_id:
            q = q.filter(StockLedger.item_id == item_id)
        if warehouse_id:
            q = q.filter(StockLedger.warehouse_id == warehouse_id)
        if reference_type:
            q = q.filter(StockLedger.reference_type == reference_type)

        return q.offset(offset).limit(limit).all()
