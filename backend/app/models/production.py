import uuid
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductionBatch(Base):
    __tablename__ = "production_batches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_number = Column(String(100), unique=True, nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    planned_quantity = Column(Integer, nullable=False)
    completed_quantity = Column(Integer, default=0)
    rejected_quantity = Column(Integer, default=0)
    status = Column(String(30), default="in_progress", index=True)  # in_progress | completed | cancelled
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    created_by = Column(String(36), ForeignKey("users.id"))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    creator = relationship("User")
    materials = relationship("ProductionBatchMaterial", back_populates="batch")
    wip_items = relationship("WIPInventory", back_populates="batch")
    wastage_records = relationship("WastageRecord", back_populates="batch")


class ProductionBatchMaterial(Base):
    __tablename__ = "production_batch_materials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("production_batches.id"), nullable=False, index=True)
    raw_material_id = Column(String(36), ForeignKey("raw_materials.id"), nullable=False)
    required_quantity = Column(Numeric(15, 4), nullable=False)
    actual_quantity = Column(Numeric(15, 4))
    wastage_expected = Column(Numeric(15, 4))
    wastage_actual = Column(Numeric(15, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("ProductionBatch", back_populates="materials")
    raw_material = relationship("RawMaterial")
