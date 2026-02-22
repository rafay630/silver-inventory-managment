"""
Product Pricing Service — Manage pricing for finished goods.

Uses WAC from StockLedgerService for cost basis.
No journal entries — pricing has no accounting impact.
"""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.product_pricing import ProductPricing
from app.models.item import Item
from app.models.stock_ledger import StockLedger
from app.services.stock_ledger_service import StockLedgerService


class ProductPricingService:

    @staticmethod
    def list_catalog(db: Session, company_id: str) -> list[dict]:
        """
        Full catalog: all active finished goods with pricing status + live WAC/stock.
        Left-joins ProductPricing so items without pricing appear as "draft".
        """
        items = db.query(Item).filter(
            Item.company_id == company_id,
            Item.item_type == "finished_good",
            Item.is_active == True,
        ).order_by(Item.name).all()

        catalog = []
        for item in items:
            wac = StockLedgerService.get_weighted_average_cost(db, company_id, item.id)
            stock = StockLedgerService.get_stock_balance(db, company_id, item.id)

            pricing = db.query(ProductPricing).filter(
                ProductPricing.company_id == company_id,
                ProductPricing.item_id == item.id,
            ).first()

            catalog.append({
                "item_id": item.id,
                "item_name": item.name,
                "item_sku": item.sku,
                "item_type": item.item_type,
                "current_wac": round(wac, 4),
                "current_stock": round(stock, 4),
                "pricing_id": pricing.id if pricing else None,
                "profit_margin_percent": pricing.profit_margin_percent if pricing else None,
                "cost_basis": pricing.cost_basis if pricing else None,
                "selling_price": pricing.selling_price if pricing else None,
                "status": pricing.status if pricing else "draft",
                "notes": pricing.notes if pricing else None,
                "updated_at": pricing.updated_at if pricing else None,
            })

        return catalog

    @staticmethod
    def upsert_pricing(
        db: Session,
        company_id: str,
        item_id: str,
        margin_percent: float,
        notes: str | None,
        user_id: str,
    ) -> ProductPricing:
        """
        Create or update pricing for a finished good.
        Snapshots WAC as cost_basis and calculates selling_price.
        Status stays as-is (draft if new, unchanged if existing).
        """
        # Validate item exists and is finished good
        item = db.query(Item).filter(
            Item.id == item_id,
            Item.company_id == company_id,
            Item.item_type == "finished_good",
        ).first()
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found or is not a finished good.",
            )

        if margin_percent < 0 or margin_percent > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Margin must be between 0% and 500%.",
            )

        # Get live WAC
        wac = StockLedgerService.get_weighted_average_cost(db, company_id, item_id)
        selling_price = round(wac * (1 + margin_percent / 100), 4)

        # Upsert
        pricing = db.query(ProductPricing).filter(
            ProductPricing.company_id == company_id,
            ProductPricing.item_id == item_id,
        ).first()

        if pricing:
            pricing.profit_margin_percent = margin_percent
            pricing.cost_basis = wac
            pricing.selling_price = selling_price
            pricing.notes = notes if notes is not None else pricing.notes
            pricing.updated_by = user_id
        else:
            pricing = ProductPricing(
                id=str(uuid.uuid4()),
                company_id=company_id,
                item_id=item_id,
                profit_margin_percent=margin_percent,
                cost_basis=wac,
                selling_price=selling_price,
                status="draft",
                notes=notes,
                created_by=user_id,
            )
            db.add(pricing)

        db.flush()
        return pricing

    @staticmethod
    def publish_product(
        db: Session,
        company_id: str,
        pricing_id: str,
        user_id: str,
    ) -> ProductPricing:
        """
        Publish a product: set status="listed".
        Re-snapshots WAC and recomputes selling price at publish time.
        """
        pricing = db.query(ProductPricing).filter(
            ProductPricing.id == pricing_id,
            ProductPricing.company_id == company_id,
        ).first()
        if not pricing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pricing record not found.",
            )

        # Re-snapshot WAC at publish time
        wac = StockLedgerService.get_weighted_average_cost(
            db, company_id, pricing.item_id
        )
        pricing.cost_basis = wac
        pricing.selling_price = round(wac * (1 + pricing.profit_margin_percent / 100), 4)
        pricing.status = "listed"
        pricing.updated_by = user_id

        db.flush()
        return pricing

    @staticmethod
    def unpublish_product(
        db: Session,
        company_id: str,
        pricing_id: str,
        user_id: str,
    ) -> ProductPricing:
        """Unpublish: set status="draft". Does NOT affect existing sales orders."""
        pricing = db.query(ProductPricing).filter(
            ProductPricing.id == pricing_id,
            ProductPricing.company_id == company_id,
        ).first()
        if not pricing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pricing record not found.",
            )

        pricing.status = "draft"
        pricing.updated_by = user_id
        db.flush()
        return pricing

    @staticmethod
    def get_listed_items(db: Session, company_id: str) -> list[dict]:
        """
        Returns only 'listed' products — used by Sales Order create modal.
        Includes live stock and WAC for display.
        """
        pricings = db.query(ProductPricing, Item).join(
            Item, ProductPricing.item_id == Item.id,
        ).filter(
            ProductPricing.company_id == company_id,
            ProductPricing.status == "listed",
            Item.is_active == True,
        ).order_by(Item.name).all()

        results = []
        for pricing, item in pricings:
            stock = StockLedgerService.get_stock_balance(db, company_id, item.id)
            wac = StockLedgerService.get_weighted_average_cost(db, company_id, item.id)
            results.append({
                "item_id": item.id,
                "item_name": item.name,
                "item_sku": item.sku,
                "selling_price": pricing.selling_price,
                "current_stock": round(stock, 4),
                "current_wac": round(wac, 4),
            })

        return results
