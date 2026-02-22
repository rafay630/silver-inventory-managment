"""
Database Seed Script — Initialize default company, admin user, UOMs, and warehouse.

Usage: python seed.py
"""
import uuid
import sys
import os

# Allow running from backend/ directory
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models.company import Company
from app.models.user import User
from app.models.uom import UOM
from app.models.warehouse import Warehouse
from app.services.auth_service import hash_password
from app.services.accounting_service import AccountingService

# Import all models
import app.models  # noqa: F401


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(Company).first()
        if existing:
            print(f"Database already seeded. Company: {existing.name} (ID: {existing.id})")
            return

        # ── Company ──
        company_id = str(uuid.uuid4())
        company = Company(
            id=company_id,
            name="Silver Manufacturing Co.",
            code="SILVER",
            address="Karachi, Pakistan",
        )
        db.add(company)
        db.flush()
        print(f"✓ Company created: {company.name} (ID: {company.id})")

        # ── Admin User ──
        admin_id = str(uuid.uuid4())
        admin = User(
            id=admin_id,
            company_id=company_id,
            username="admin",
            email="admin@silver.com",
            password_hash=hash_password("admin123"),
            full_name="System Admin",
            role="admin",
        )
        db.add(admin)
        print("✓ Admin user created: admin / admin123")

        # ── UOMs ──
        uoms = [
            ("Grams", "g"),
            ("Kilograms", "kg"),
            ("Pieces", "pcs"),
            ("Meters", "m"),
            ("Liters", "L"),
            ("Ounces", "oz"),
            ("Troy Ounces", "toz"),
        ]
        uom_ids = {}
        for name, abbr in uoms:
            uom = UOM(
                id=str(uuid.uuid4()),
                company_id=company_id,
                name=name,
                abbreviation=abbr,
            )
            db.add(uom)
            uom_ids[abbr] = uom.id
        print(f"✓ {len(uoms)} UOMs created")

        # ── Warehouse ──
        wh = Warehouse(
            id=str(uuid.uuid4()),
            company_id=company_id,
            name="Main Warehouse",
            code="WH-MAIN",
            address="Factory Floor 1",
        )
        db.add(wh)
        print(f"✓ Warehouse created: {wh.name} ({wh.code})")

        # ── Chart of Accounts ──
        AccountingService.seed_chart_of_accounts(db, company_id)
        print("✓ Chart of Accounts seeded (18 system accounts)")

        db.commit()
        print("\n═══ Seed completed successfully ═══")
        print(f"\nCompany ID: {company_id}")
        print(f"Admin credentials: admin / admin123")
        print(f"\nUOM IDs: {uom_ids}")
        print(f"Warehouse ID: {wh.id}")

    except Exception as e:
        db.rollback()
        print(f"✗ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
