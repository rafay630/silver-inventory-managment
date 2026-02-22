"""Auth Router — Login, Register, Company Setup."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.schemas.user import UserCreate, UserLogin, UserOut, Token, CompanyCreate, CompanyOut
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.services.accounting_service import AccountingService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register-company", response_model=CompanyOut, status_code=201)
def register_company(data: CompanyCreate, db: Session = Depends(get_db)):
    """Register a new company and seed its chart of accounts."""
    exists = db.query(Company).filter(Company.code == data.code).first()
    if exists:
        raise HTTPException(status_code=400, detail="Company code already exists")

    company = Company(
        id=str(uuid.uuid4()),
        name=data.name,
        code=data.code,
        address=data.address,
        phone=data.phone,
        email=data.email,
    )
    db.add(company)
    db.flush()

    # Seed chart of accounts
    AccountingService.seed_chart_of_accounts(db, company.id)
    db.commit()
    db.refresh(company)
    return company


@router.post("/register", response_model=UserOut, status_code=201)
def register_user(data: UserCreate, company_id: str, db: Session = Depends(get_db)):
    """Register a user within an existing company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    existing = db.query(User).filter(
        User.company_id == company_id,
        User.username == data.username,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken in this company")

    valid_roles = ["admin", "accountant", "production_manager", "store_manager"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {', '.join(valid_roles)}")

    user = User(
        id=str(uuid.uuid4()),
        company_id=company_id,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and return JWT token."""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(user.id, user.company_id, user.role)
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
