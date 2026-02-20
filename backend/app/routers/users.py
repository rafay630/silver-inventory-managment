from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    return db.query(User).all()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if update.role is not None:
        user.role = update.role
    if update.is_active is not None:
        user.is_active = update.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"detail": "User deactivated"}
