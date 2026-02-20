import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WastageRecord(Base):
    __tablename__ = "wastage_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String(36), ForeignKey("production_batches.id"), nullable=False, index=True)
    raw_material_id = Column(String(36), ForeignKey("raw_materials.id"), nullable=False)
    expected_wastage = Column(Numeric(15, 4))
    actual_wastage = Column(Numeric(15, 4))
    variance = Column(Numeric(15, 4))
    variance_percent = Column(Numeric(8, 2))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("ProductionBatch", back_populates="wastage_records")
    raw_material = relationship("RawMaterial")
