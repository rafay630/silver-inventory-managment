"""Production Orders Router — Create, manage, and complete production orders."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.production import ProductionOrder
from app.models.user import User
from app.dependencies import get_current_user, require_roles
from app.schemas.production import (
    ProductionOrderCreate, ProductionOrderOut,
    WIPIssueCreate, WIPIssueOut,
    ProductionExpenseCreate, ProductionExpenseOut,
    ProductionCompletionRequest,
)
from app.services.production_service import ProductionService
from app.services.wip_service import WIPService
from app.services.expense_service import ExpenseService
from app.services.completion_service import CompletionService
from typing import List, Optional

router = APIRouter(prefix="/api/production-orders", tags=["Production"])


# ═══ Production Orders ═══
@router.post("/", response_model=ProductionOrderOut, status_code=201)
def create_production_order(
    data: ProductionOrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["admin", "production_manager"])),
):
    order = ProductionService.create_production_order(
        db=db,
        company_id=user.company_id,
        product_id=data.product_id,
        bom_id=data.bom_id,
        order_qty=data.order_qty,
        warehouse_id=data.warehouse_id,
        start_date=data.start_date,
        end_date=data.end_date,
        notes=data.notes,
        created_by=user.id,
    )
    db.commit()
    db.refresh(order)
    return order


@router.get("/", response_model=List[ProductionOrderOut])
def list_production_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(ProductionOrder).filter(ProductionOrder.company_id == user.company_id)
    if status:
        q = q.filter(ProductionOrder.status == status)
    return q.order_by(ProductionOrder.created_at.desc()).all()


@router.get("/{order_id}", response_model=ProductionOrderOut)
def get_production_order(order_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(ProductionOrder).filter(
        ProductionOrder.id == order_id,
        ProductionOrder.company_id == user.company_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Production order not found")
    return order


@router.post("/{order_id}/start", response_model=ProductionOrderOut)
def start_production(order_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(["admin", "production_manager"]))):
    order = ProductionService.start_production(db, user.company_id, order_id)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=ProductionOrderOut)
def cancel_production(order_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles(["admin", "production_manager"]))):
    order = ProductionService.cancel_production(db, user.company_id, order_id)
    db.commit()
    db.refresh(order)
    return order


# ═══ WIP Issues ═══
@router.post("/{order_id}/wip-issues", response_model=WIPIssueOut, status_code=201)
def issue_materials(
    order_id: str,
    data: WIPIssueCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["admin", "production_manager", "store_manager"])),
):
    """Issue raw materials from warehouse to production (WIP)."""
    if data.production_order_id != order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")
    issue = WIPService.issue_materials(
        db=db,
        company_id=user.company_id,
        production_order_id=order_id,
        issue_date=data.issue_date,
        items=[item.model_dump() for item in data.items],
        created_by=user.id,
    )
    db.commit()
    db.refresh(issue)
    return issue


# ═══ Production Expenses ═══
@router.post("/{order_id}/expenses", response_model=ProductionExpenseOut, status_code=201)
def record_expense(
    order_id: str,
    data: ProductionExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["admin", "accountant", "production_manager"])),
):
    """Record a production expense with absorption costing."""
    if data.production_order_id != order_id:
        raise HTTPException(status_code=400, detail="Order ID mismatch")
    expense = ExpenseService.record_expense(
        db=db,
        company_id=user.company_id,
        production_order_id=order_id,
        expense_type=data.expense_type,
        amount=data.amount,
        expense_date=data.expense_date,
        description=data.description,
        created_by=user.id,
    )
    db.commit()
    db.refresh(expense)
    return expense


# ═══ Production Completion ═══
@router.post("/{order_id}/complete")
def complete_production(
    order_id: str,
    data: ProductionCompletionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(["admin", "production_manager"])),
):
    """Complete production — calculates costs, creates finished goods, journals."""
    result = CompletionService.complete_production(
        db=db,
        company_id=user.company_id,
        order_id=order_id,
        completed_qty=data.completed_qty,
        completion_date=data.completion_date,
        created_by=user.id,
    )
    db.commit()
    return result
