"""
Production Order Service — Create orders, calculate requirements, manage lifecycle.
"""
import uuid
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.production import ProductionOrder, ProductionRequirement
from app.models.bom import BOM
from app.models.item import Item
from app.services.bom_service import BOMService
from app.services.stock_ledger_service import StockLedgerService


class ProductionService:

    @staticmethod
    def _next_order_number(db: Session, company_id: str) -> str:
        count = db.query(func.count(ProductionOrder.id)).filter(
            ProductionOrder.company_id == company_id,
        ).scalar() or 0
        return f"PO-{count + 1:06d}"

    @staticmethod
    def create_production_order(
        db: Session,
        company_id: str,
        product_id: str,
        bom_id: str,
        order_qty: float,
        warehouse_id: str,
        start_date: date = None,
        end_date: date = None,
        notes: str = "",
        created_by: str = None,
    ) -> ProductionOrder:
        """
        Create a production order:
        1) Validate product & BOM
        2) Calculate material requirements using BOM formula
        3) Snapshot requirements into production_requirements table
        4) Check stock availability and mark adequate/insufficient
        """
        # Validate BOM belongs to product
        bom = db.query(BOM).filter(
            BOM.id == bom_id,
            BOM.company_id == company_id,
            BOM.product_id == product_id,
        ).first()
        if not bom:
            raise HTTPException(status_code=400, detail="BOM not found or doesn't match product")

        order = ProductionOrder(
            id=str(uuid.uuid4()),
            company_id=company_id,
            order_number=ProductionService._next_order_number(db, company_id),
            product_id=product_id,
            bom_id=bom_id,
            order_qty=order_qty,
            warehouse_id=warehouse_id,
            status="planned",
            start_date=start_date,
            end_date=end_date,
            notes=notes,
            created_by=created_by,
        )
        db.add(order)
        db.flush()

        # Calculate requirements using BOM
        requirements = BOMService.calculate_requirements(db, bom_id, order_qty)

        all_adequate = True
        for req in requirements:
            available = StockLedgerService.get_stock_balance(
                db, company_id, req["item_id"], warehouse_id,
            )
            req_status = "adequate" if available >= req["required_qty"] else "insufficient"
            if req_status == "insufficient":
                all_adequate = False

            pr = ProductionRequirement(
                id=str(uuid.uuid4()),
                production_order_id=order.id,
                item_id=req["item_id"],
                required_qty=req["required_qty"],
                available_qty=available,
                status=req_status,
            )
            db.add(pr)

        db.flush()
        return order

    @staticmethod
    def start_production(db: Session, company_id: str, order_id: str) -> ProductionOrder:
        """Transition order to in_progress."""
        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == order_id,
            ProductionOrder.company_id == company_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Production order not found")
        if order.status != "planned":
            raise HTTPException(status_code=400, detail=f"Cannot start order in '{order.status}' status")

        order.status = "in_progress"
        db.flush()
        return order

    @staticmethod
    def cancel_production(db: Session, company_id: str, order_id: str) -> ProductionOrder:
        """Cancel order — only if no WIP issues have been made."""
        from app.models.wip import WIPIssue

        order = db.query(ProductionOrder).filter(
            ProductionOrder.id == order_id,
            ProductionOrder.company_id == company_id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Production order not found")
        if order.status == "completed":
            raise HTTPException(status_code=400, detail="Cannot cancel a completed order")

        # Check for existing WIP issues
        wip_count = db.query(func.count(WIPIssue.id)).filter(
            WIPIssue.production_order_id == order_id,
        ).scalar()
        if wip_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel order with existing WIP issues. Reverse issues first.",
            )

        order.status = "cancelled"
        db.flush()
        return order
