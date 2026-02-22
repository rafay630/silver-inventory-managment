import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UOM(Base):
    __tablename__ = "uom"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")

    __table_args__ = (
        Index("ix_uom_company_name", "company_id", "name", unique=True),
    )


class UOMConversion(Base):
    __tablename__ = "uom_conversions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False, index=True)
    from_uom_id = Column(String(36), ForeignKey("uom.id"), nullable=False, index=True)
    to_uom_id = Column(String(36), ForeignKey("uom.id"), nullable=False, index=True)
    conversion_factor = Column(Numeric(18, 8), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    from_uom = relationship("UOM", foreign_keys=[from_uom_id])
    to_uom = relationship("UOM", foreign_keys=[to_uom_id])

    __table_args__ = (
        Index("ix_uom_conv_company_from_to", "company_id", "from_uom_id", "to_uom_id", unique=True),
    )
