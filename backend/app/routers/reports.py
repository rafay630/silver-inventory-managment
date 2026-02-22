"""Reports Router — All 8 required reports."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.services.report_service import ReportService
from typing import Optional
from datetime import date

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/stock-ledger")
def stock_ledger_report(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stock Ledger Report with running balances."""
    return ReportService.stock_ledger_report(db, user.company_id, item_id, warehouse_id, from_date, to_date)


@router.get("/inventory-valuation")
def inventory_valuation(
    warehouse_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Inventory Valuation (Weighted Average)."""
    return ReportService.inventory_valuation(db, user.company_id, warehouse_id)


@router.get("/production-cost-sheet/{order_id}")
def production_cost_sheet(
    order_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Detailed production order cost breakdown."""
    return ReportService.production_cost_sheet(db, user.company_id, order_id)


@router.get("/wip-summary")
def wip_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """WIP Summary — all in-progress production orders with costs."""
    return ReportService.wip_summary(db, user.company_id)


@router.get("/material-consumption")
def material_consumption(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Material Consumption Report grouped by item."""
    return ReportService.material_consumption_report(db, user.company_id, from_date, to_date)


@router.get("/trial-balance")
def trial_balance(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ReportService.trial_balance(db, user.company_id, as_of_date)


@router.get("/profit-and-loss")
def profit_and_loss(
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ReportService.profit_and_loss(db, user.company_id, from_date, to_date)


@router.get("/balance-sheet")
def balance_sheet(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ReportService.balance_sheet(db, user.company_id, as_of_date)
