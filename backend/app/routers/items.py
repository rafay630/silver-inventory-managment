"""Items, Categories, UOMs, and Warehouses Router."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.item import Item
from app.models.category import Category
from app.models.uom import UOM, UOMConversion
from app.models.warehouse import Warehouse
from app.models.user import User
from app.dependencies import get_current_user, require_roles
from app.schemas.inventory import (
    CategoryCreate, CategoryOut,
    UOMCreate, UOMOut, UOMConversionCreate, UOMConversionOut,
    ItemCreate, ItemUpdate, ItemOut,
    WarehouseCreate, WarehouseUpdate, WarehouseOut,
    StockBalanceOut,
)
from app.services.stock_ledger_service import StockLedgerService
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["Inventory Master"])


# ═══ Categories ═══
@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cat = Category(id=str(uuid.uuid4()), company_id=user.company_id, name=data.name, description=data.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.get("/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Category).filter(Category.company_id == user.company_id).all()


# ═══ UOMs ═══
@router.post("/uom", response_model=UOMOut, status_code=201)
def create_uom(data: UOMCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    uom = UOM(id=str(uuid.uuid4()), company_id=user.company_id, name=data.name, abbreviation=data.abbreviation)
    db.add(uom)
    db.commit()
    db.refresh(uom)
    return uom

@router.get("/uom", response_model=List[UOMOut])
def list_uoms(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UOM).filter(UOM.company_id == user.company_id).all()

@router.post("/uom/conversions", response_model=UOMConversionOut, status_code=201)
def create_uom_conversion(data: UOMConversionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = UOMConversion(
        id=str(uuid.uuid4()),
        company_id=user.company_id,
        from_uom_id=data.from_uom_id,
        to_uom_id=data.to_uom_id,
        conversion_factor=data.conversion_factor,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/uom/conversions", response_model=List[UOMConversionOut])
def list_uom_conversions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(UOMConversion).filter(UOMConversion.company_id == user.company_id).all()


# ═══ Items ═══
@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(data: ItemCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.item_type not in ("raw_material", "finished_good"):
        raise HTTPException(status_code=400, detail="item_type must be 'raw_material' or 'finished_good'")
    item = Item(
        id=str(uuid.uuid4()),
        company_id=user.company_id,
        name=data.name,
        sku=data.sku,
        barcode=data.barcode,
        description=data.description,
        item_type=data.item_type,
        category_id=data.category_id,
        uom_id=data.uom_id,
        base_cost=data.base_cost,
        reorder_level=data.reorder_level,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/items", response_model=List[ItemOut])
def list_items(
    item_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Item).filter(Item.company_id == user.company_id)
    if item_type:
        q = q.filter(Item.item_type == item_type)
    if is_active is not None:
        q = q.filter(Item.is_active == is_active)
    return q.order_by(Item.name).all()

@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id, Item.company_id == user.company_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: str, data: ItemUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id, Item.company_id == user.company_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item

@router.get("/items/barcode/{barcode}", response_model=ItemOut)
def get_item_by_barcode(barcode: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(Item).filter(Item.barcode == barcode, Item.company_id == user.company_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found with this barcode")
    return item


# ═══ Warehouses ═══
@router.post("/warehouses", response_model=WarehouseOut, status_code=201)
def create_warehouse(data: WarehouseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wh = Warehouse(
        id=str(uuid.uuid4()),
        company_id=user.company_id,
        name=data.name,
        code=data.code,
        address=data.address,
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh

@router.get("/warehouses", response_model=List[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Warehouse).filter(Warehouse.company_id == user.company_id).all()

@router.put("/warehouses/{warehouse_id}", response_model=WarehouseOut)
def update_warehouse(warehouse_id: str, data: WarehouseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    wh = db.query(Warehouse).filter(Warehouse.id == warehouse_id, Warehouse.company_id == user.company_id).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(wh, field, value)
    db.commit()
    db.refresh(wh)
    return wh

@router.get("/warehouses/{warehouse_id}/stock", response_model=List[StockBalanceOut])
def get_warehouse_stock(warehouse_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return StockLedgerService.get_all_balances(db, user.company_id, warehouse_id=warehouse_id)
