from typing import Annotated
from uuid import uuid4, UUID
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional


class StudentForTeacher(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    class_name : str | None = Field(default=None)
    contact: str | None = Field(default=None)
    address: str | None = Field(default=None)
    
class UserForStudent(SQLModel):
    id: UUID
    email: str
    
class ClassForTeacher(SQLModel):
    id: UUID
    name: str = Field(index=True)
    

class TeacherCreate(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    contact: str | None = Field(default=None)
    subject: str | None = Field(default=None)
    address: str | None = Field(default=None)
    user_id: UUID | None = Field(default=None, foreign_key="users.id", unique=True)  
    
class Teacher(TeacherCreate, table=True):
    __tablename__ = "teachers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)   
    classroom: Optional["Classroom"] = Relationship(back_populates="teacher")  # this name will be name of field not the name of table
    user: Optional["User"] = Relationship(back_populates="teacher_profile")
    
class TeacherRead(SQLModel):  # I need to create this model so that I can show parents array
    id: UUID
    name: str
    age: int | None
    contact: str | None
    subject: str | None
    address: str | None  
    classroom: Optional[ClassForTeacher] = None
    user: Optional[UserForStudent] = None
    
