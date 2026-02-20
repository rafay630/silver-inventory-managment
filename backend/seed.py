"""Seed script — creates the first admin user."""
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.services.auth_service import get_password_hash

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if admin already exists
existing = db.query(User).filter(User.username == "admin").first()
if existing:
    print("✓ Admin user already exists")
else:
    admin = User(
        username="admin",
        email="admin@silverinventory.com",
        password_hash=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("✓ Admin user created!")
    print("  Username: admin")
    print("  Password: admin123")

db.close()
