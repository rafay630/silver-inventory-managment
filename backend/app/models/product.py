import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    sku = Column(String(100), unique=True, index=True)
    description = Column(Text)
    wastage_percent = Column(Numeric(5, 2), nullable=False, default=0)
    unit = Column(String(20), default="pieces")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bom_items = relationship("BillOfMaterial", back_populates="product")


class BillOfMaterial(Base):
    __tablename__ = "bill_of_materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    raw_material_id = Column(String(36), ForeignKey("raw_materials.id"), nullable=False)
    quantity_per_unit = Column(Numeric(15, 4), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="bom_items")
    raw_material = relationship("RawMaterial")

    __table_args__ = (
        UniqueConstraint("product_id", "raw_material_id", name="uq_bom_product_material"),
    )
