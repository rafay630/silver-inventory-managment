"""
BOM Service — Bill of Materials management with versioning.
"""
import uuid
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.bom import BOM, BOMItem
from app.models.item import Item


class BOMService:

    @staticmethod
    def create_bom(
        db: Session,
        company_id: str,
        product_id: str,
        version: str,
        is_active: bool,
        notes: str,
        items: list[dict],
        created_by: str,
    ) -> BOM:
        """Create a new BOM version. If is_active, deactivate previous active BOMs."""
        # Validate product is a finished good
        product = db.query(Item).filter(
            Item.id == product_id,
            Item.company_id == company_id,
            Item.item_type == "finished_good",
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found or not a finished good")

        # Check version uniqueness
        exists = db.query(BOM).filter(
            BOM.company_id == company_id,
            BOM.product_id == product_id,
            BOM.version == version,
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail=f"BOM version '{version}' already exists for this product")

        # If marking as active, deactivate other versions
        if is_active:
            db.query(BOM).filter(
                BOM.company_id == company_id,
                BOM.product_id == product_id,
                BOM.is_active == True,
            ).update({"is_active": False})

        bom = BOM(
            id=str(uuid.uuid4()),
            company_id=company_id,
            product_id=product_id,
            version=version,
            is_active=is_active,
            notes=notes,
            created_by=created_by,
        )
        db.add(bom)
        db.flush()

        # Add BOM items
        for item_data in items:
            # Validate raw material exists
            raw_item = db.query(Item).filter(
                Item.id == item_data["raw_item_id"],
                Item.company_id == company_id,
                Item.item_type == "raw_material",
            ).first()
            if not raw_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Raw material '{item_data['raw_item_id']}' not found",
                )

            bom_item = BOMItem(
                id=str(uuid.uuid4()),
                bom_id=bom.id,
                raw_item_id=item_data["raw_item_id"],
                quantity=item_data["quantity"],
                wastage_percent=item_data.get("wastage_percent", 0),
                uom_id=item_data.get("uom_id"),
                conversion_factor=item_data.get("conversion_factor", 1),
            )
            db.add(bom_item)

        db.flush()
        return bom

    @staticmethod
    def calculate_requirements(
        db: Session,
        bom_id: str,
        order_qty: float,
    ) -> list[dict]:
        """
        Calculate material requirements for a given order quantity.
        Formula: required_qty = order_qty × bom_qty × (1 + wastage_percent / 100)
        """
        bom = db.query(BOM).filter(BOM.id == bom_id).first()
        if not bom:
            raise HTTPException(status_code=404, detail="BOM not found")

        requirements = []
        for bom_item in bom.items:
            bom_qty = float(bom_item.quantity)
            wastage = float(bom_item.wastage_percent)
            conv = float(bom_item.conversion_factor)

            required = order_qty * bom_qty * (1 + wastage / 100) * conv
            requirements.append({
                "item_id": bom_item.raw_item_id,
                "required_qty": round(required, 4),
                "bom_qty": bom_qty,
                "wastage_percent": wastage,
                "conversion_factor": conv,
            })

        return requirements

    @staticmethod
    def get_active_bom(db: Session, company_id: str, product_id: str) -> BOM | None:
        """Get the currently active BOM for a product."""
        return db.query(BOM).filter(
            BOM.company_id == company_id,
            BOM.product_id == product_id,
            BOM.is_active == True,
        ).first()
