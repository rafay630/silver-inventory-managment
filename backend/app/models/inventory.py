import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WIPInventory(Base):
    __tablename__ = "wip_inventory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("production_batches.id"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    status = Column(String(30), default="in_process", index=True)  # in_process | completed | rejected
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("ProductionBatch", back_populates="wip_items")
    product = relationship("Product")


class FinishedGoods(Base):
    __tablename__ = "finished_goods"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    batch_id = Column(String(36), ForeignKey("production_batches.id"), index=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    location = Column(String(100), default="main_warehouse")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    batch = relationship("ProductionBatch")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_type = Column(String(50), nullable=False, index=True)
    raw_material_id = Column(String(36), ForeignKey("raw_materials.id"), index=True)
    product_id = Column(String(36), ForeignKey("products.id"), index=True)
    batch_id = Column(String(36), ForeignKey("production_batches.id"), index=True)
    quantity = Column(Numeric(15, 4), nullable=False)
    unit = Column(String(20))
    reference_number = Column(String(100))
    notes = Column(Text)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    raw_material = relationship("RawMaterial")
    product = relationship("Product")
    batch = relationship("ProductionBatch")
    creator = relationship("User")
