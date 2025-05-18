from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from database import get_session  # your db session
from models.users import User
from Utilities.security import hash_password, verify_password
from Utilities.token import create_access_token
from pydantic import BaseModel
from Utilities.auth import get_current_user, require_min_role
from typing import List
from Utilities.auth import require_min_role


router = APIRouter()

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str = "student"  # default role

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, hashed_password=hash_password(data.password), role=data.role)
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
    return {"access_token": token, "token_type": "bearer", "role": user.role, "student_profile": user.student_profile, "teacher_profile": user.teacher_profile}

@router.get("/me")
def read_profile(user: User = Depends(get_current_user)):
    return {"email": user.email, "role": user.role}

@router.get("/admin-area")
def admin_area(user: User = Depends(require_min_role("admin"))):
    return {"message": "Welcome Admin!"}

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