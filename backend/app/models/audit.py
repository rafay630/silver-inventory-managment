import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    action = Column(String(50), nullable=False, index=True)
    # Actions: create, update, delete
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(36), index=True)
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        Index("ix_audit_company_entity", "company_id", "entity_type", "entity_id"),
        Index("ix_audit_created", "created_at"),
    )
