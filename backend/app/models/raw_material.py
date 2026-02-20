import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    material_type = Column(String(50), nullable=False)  # SILVER | BRASS
    unit = Column(String(20), nullable=False, default="grams")
    reorder_level = Column(Numeric(15, 4), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    stocks = relationship("RawMaterialStock", back_populates="raw_material")


class RawMaterialStock(Base):
    __tablename__ = "raw_material_stock"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    raw_material_id = Column(String(36), ForeignKey("raw_materials.id"), nullable=False, index=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), index=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit_price = Column(Numeric(15, 4))
    purchase_date = Column(Date, nullable=False)
    invoice_number = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    raw_material = relationship("RawMaterial", back_populates="stocks")
    supplier = relationship("Supplier")
