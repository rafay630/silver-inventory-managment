"""Stock Ledger Router — Read-only access to stock movements and balances."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user
from app.schemas.inventory import StockLedgerOut, StockBalanceOut
from app.services.stock_ledger_service import StockLedgerService
from typing import List, Optional

router = APIRouter(prefix="/api/stock-ledger", tags=["Stock Ledger"])


@router.get("/entries", response_model=List[StockLedgerOut])
def list_ledger_entries(
    item_id: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return StockLedgerService.get_ledger_entries(
        db, user.company_id, item_id, warehouse_id, reference_type, limit, offset,
    )


@router.get("/balance")
def get_stock_balance(
    item_id: str,
    warehouse_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    balance = StockLedgerService.get_stock_balance(db, user.company_id, item_id, warehouse_id)
    wac = StockLedgerService.get_weighted_average_cost(db, user.company_id, item_id, warehouse_id)
    return {
        "item_id": item_id,
        "warehouse_id": warehouse_id,
        "balance": balance,
        "weighted_avg_cost": wac,
        "total_value": round(balance * wac, 4),
    }


@router.get("/balances", response_model=List[StockBalanceOut])
def get_all_balances(
    item_type: Optional[str] = None,
    warehouse_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return StockLedgerService.get_all_balances(db, user.company_id, item_type, warehouse_id)
