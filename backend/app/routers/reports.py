from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.report_service import (
    get_stock_report,
    get_wastage_report,
    get_efficiency_report,
    get_wip_summary,
    get_batch_history,
    get_consumption_variance,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/raw-material-stock")
def raw_material_stock_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_stock_report(db)


@router.get("/wastage")
def wastage_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_wastage_report(db)


@router.get("/production-efficiency")
def production_efficiency_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_efficiency_report(db)


@router.get("/wip-summary")
def wip_summary_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_wip_summary(db)


@router.get("/batch-history")
def batch_history_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_batch_history(db)


@router.get("/consumption-variance")
def consumption_variance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_consumption_variance(db)
