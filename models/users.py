from sqlmodel import SQLModel, Field,Relationship
from typing import Optional
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    __tablename__= "users"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: str # default role
    student_profile: Optional["Student"] = Relationship(back_populates="user")
    teacher_profile: Optional["Teacher"] | None = Relationship(back_populates="user")
    

class AdminPasswordResetRequest(SQLModel):
    user_email: str
    new_password: str