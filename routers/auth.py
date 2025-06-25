from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlmodel import Session, select
from database import get_session
from models.users import User, AdminPasswordResetRequest
from Utilities.security import hash_password, verify_password
from Utilities.token import create_access_token
from pydantic import BaseModel
from Utilities.auth import get_current_user, require_min_role
from typing import List
from uuid import UUID

router = APIRouter()


# ----------------------
# Pydantic Models
# ----------------------

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "student"  # default role


class LoginRequest(BaseModel):
    email: str
    password: str


# ----------------------
# Authentication Routes
# ----------------------

@router.post("/register")
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "email": user.email}


@router.post("/login")
def login(data: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "student_profile": user.student_profile,
        "teacher_profile": user.teacher_profile,
        "id": str(user.id)
    }


# ----------------------
# User Info & Admin Area
# ----------------------

@router.get("/me")
def read_profile(user: User = Depends(get_current_user)):
    return {
        "email": user.email,
        "role": user.role,
        "student_profile": user.student_profile,
        "teacher_profile": user.teacher_profile
    }


@router.get("/admin-area")
def admin_area(user: User = Depends(require_min_role("admin"))):
    return {"message": "Welcome Admin!"}


# ----------------------
# User Management (Admin)
# ----------------------

@router.get("/users", response_model=List[User])
def get_all_users(
    session: Session = Depends(get_session),
    _: User = Depends(require_min_role("admin")),
    limit: int = Query(10, ge=1, le=100),
    page: int = Query(1, ge=1)
):
    offset = (page - 1) * limit
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users


@router.post("/admin/reset-password")
def admin_reset_password(
    data: AdminPasswordResetRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_min_role("admin")),
):
    user = session.exec(select(User).where(User.email == data.user_email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(data.new_password)
    session.add(user)
    session.commit()

    return {"message": f"Password for {user.email} has been reset successfully"}


@router.delete("/users/{user_id}")
def delete_user_by_id(
    user_id: UUID = Path(..., description="ID of the user to delete"),
    session: Session = Depends(get_session),
    _: User = Depends(require_min_role("admin"))
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()

    return {"message": f"User with ID {user_id} deleted successfully"}
