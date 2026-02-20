from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, BOMItemCreate, BOMItemUpdate, BOMItemResponse
from app.dependencies import get_current_user, require_roles
from app.models.product import Product, BillOfMaterial
from app.models.raw_material import RawMaterial
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("/", response_model=List[ProductResponse])
def list_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    products = db.query(Product).filter(Product.is_active == True).all()
    result = []
    for p in products:
        bom_items = []
        for b in p.bom_items:
            rm = db.query(RawMaterial).filter(RawMaterial.id == b.raw_material_id).first()
            bom_items.append(BOMItemResponse(
                id=b.id,
                product_id=b.product_id,
                raw_material_id=b.raw_material_id,
                raw_material_name=rm.name if rm else None,
                raw_material_type=rm.material_type if rm else None,
                quantity_per_unit=b.quantity_per_unit,
                created_at=b.created_at,
            ))
        result.append(ProductResponse(
            id=p.id,
            name=p.name,
            sku=p.sku,
            description=p.description,
            wastage_percent=p.wastage_percent,
            unit=p.unit,
            is_active=p.is_active,
            bom_items=bom_items,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))
    return result


@router.post("/", response_model=ProductResponse)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse(
        id=product.id,
        name=product.name,
        sku=product.sku,
        description=product.description,
        wastage_percent=product.wastage_percent,
        unit=product.unit,
        is_active=product.is_active,
        bom_items=[],
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}/bom", response_model=List[BOMItemResponse])
def get_bom(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(BillOfMaterial).filter(BillOfMaterial.product_id == product_id).all()
    result = []
    for b in items:
        rm = db.query(RawMaterial).filter(RawMaterial.id == b.raw_material_id).first()
        result.append(BOMItemResponse(
            id=b.id,
            product_id=b.product_id,
            raw_material_id=b.raw_material_id,
            raw_material_name=rm.name if rm else None,
            raw_material_type=rm.material_type if rm else None,
            quantity_per_unit=b.quantity_per_unit,
            created_at=b.created_at,
        ))
    return result


@router.post("/{product_id}/bom", response_model=BOMItemResponse)
def add_bom_item(
    product_id: UUID,
    data: BOMItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    material = db.query(RawMaterial).filter(RawMaterial.id == data.raw_material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")

    # Check for duplicate
    existing = db.query(BillOfMaterial).filter(
        BillOfMaterial.product_id == product_id,
        BillOfMaterial.raw_material_id == data.raw_material_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="BOM item already exists for this material")

    bom = BillOfMaterial(
        product_id=product_id,
        raw_material_id=data.raw_material_id,
        quantity_per_unit=data.quantity_per_unit,
    )
    db.add(bom)
    db.commit()
    db.refresh(bom)

    return BOMItemResponse(
        id=bom.id,
        product_id=bom.product_id,
        raw_material_id=bom.raw_material_id,
        raw_material_name=material.name,
        raw_material_type=material.material_type,
        quantity_per_unit=bom.quantity_per_unit,
        created_at=bom.created_at,
    )


@router.put("/{product_id}/bom/{bom_id}", response_model=BOMItemResponse)
def update_bom_item(
    product_id: UUID,
    bom_id: UUID,
    data: BOMItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    bom = db.query(BillOfMaterial).filter(
        BillOfMaterial.id == bom_id,
        BillOfMaterial.product_id == product_id,
    ).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM item not found")

    if data.quantity_per_unit is not None:
        bom.quantity_per_unit = data.quantity_per_unit

    db.commit()
    db.refresh(bom)

    rm = db.query(RawMaterial).filter(RawMaterial.id == bom.raw_material_id).first()
    return BOMItemResponse(
        id=bom.id,
        product_id=bom.product_id,
        raw_material_id=bom.raw_material_id,
        raw_material_name=rm.name if rm else None,
        raw_material_type=rm.material_type if rm else None,
        quantity_per_unit=bom.quantity_per_unit,
        created_at=bom.created_at,
    )
