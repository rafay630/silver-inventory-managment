from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.wastage import WastageRecord


def calculate_expected_wastage(gross_required: Decimal, wastage_percent: Decimal) -> Decimal:
    """Calculate expected wastage from gross requirement and wastage percentage."""
    return gross_required * (wastage_percent / Decimal("100"))


def record_expected_wastage(
    db: Session, batch_id: UUID, raw_material_id: UUID, expected_wastage: Decimal
) -> WastageRecord:
    """Create a wastage record with expected values (actual filled on completion)."""
    record = WastageRecord(
        batch_id=batch_id,
        raw_material_id=raw_material_id,
        expected_wastage=expected_wastage,
    )
    db.add(record)
    return record


def update_actual_wastage(
    db: Session, batch_id: UUID, raw_material_id: UUID, actual_wastage: Decimal
) -> WastageRecord:
    """Update wastage record with actual values and compute variance."""
    record = db.query(WastageRecord).filter(
        WastageRecord.batch_id == batch_id,
        WastageRecord.raw_material_id == raw_material_id,
    ).first()

    if record:
        record.actual_wastage = actual_wastage
        record.variance = actual_wastage - (record.expected_wastage or Decimal("0"))
        if record.expected_wastage and record.expected_wastage > 0:
            record.variance_percent = (record.variance / record.expected_wastage) * Decimal("100")
        else:
            record.variance_percent = Decimal("0")
        db.add(record)
    return record
