"""
Product Pricing Router — Sales Catalog & Pricing endpoints.

Prefix: /api/pricing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_roles, get_company_id
from app.models.user import User
from app.services.product_pricing_service import ProductPricingService
from app.schemas.product_pricing import ProductPricingCreate, ProductPricingUpdate

router = APIRouter(prefix="/api/pricing", tags=["Sales Catalog"])


# ── GET /catalog — Full catalog (all FG with pricing info) ──
@router.get("/catalog")
def get_catalog(
    db: Session = Depends(get_db),
    company_id: str = Depends(get_company_id),
):
    """Full catalog — all finished goods with pricing status, WAC, stock."""
    return ProductPricingService.list_catalog(db, company_id)


# ── POST / — Create or update pricing ──
@router.post("/", status_code=status.HTTP_201_CREATED)
def set_pricing(
    data: ProductPricingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """Set/update margin for a finished good. Admin only."""
    pricing = ProductPricingService.upsert_pricing(
        db,
        current_user.company_id,
        data.item_id,
        data.profit_margin_percent,
        data.notes,
        current_user.id,
    )
    db.commit()
    db.refresh(pricing)
    return {
        "id": pricing.id,
        "item_id": pricing.item_id,
        "profit_margin_percent": pricing.profit_margin_percent,
        "cost_basis": pricing.cost_basis,
        "selling_price": pricing.selling_price,
        "status": pricing.status,
        "notes": pricing.notes,
    }


# ── POST /{id}/publish — Publish product ──
@router.post("/{pricing_id}/publish")
def publish_product(
    pricing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """Publish product → status = 'listed'. Admin only."""
    pricing = ProductPricingService.publish_product(
        db, current_user.company_id, pricing_id, current_user.id,
    )
    db.commit()
    db.refresh(pricing)
    return {
        "id": pricing.id,
        "item_id": pricing.item_id,
        "selling_price": pricing.selling_price,
        "cost_basis": pricing.cost_basis,
        "status": pricing.status,
    }


# ── POST /{id}/unpublish — Unpublish product ──
@router.post("/{pricing_id}/unpublish")
def unpublish_product(
    pricing_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """Unpublish product → status = 'draft'. Admin only."""
    pricing = ProductPricingService.unpublish_product(
        db, current_user.company_id, pricing_id, current_user.id,
    )
    db.commit()
    db.refresh(pricing)
    return {
        "id": pricing.id,
        "item_id": pricing.item_id,
        "status": pricing.status,
    }


# ── GET /listed — Only listed products (for Sales Order dropdown) ──
@router.get("/listed")
def get_listed_items(
    db: Session = Depends(get_db),
    company_id: str = Depends(get_company_id),
):
    """Only listed products — for Sales Order item dropdown."""
    return ProductPricingService.get_listed_items(db, company_id)
