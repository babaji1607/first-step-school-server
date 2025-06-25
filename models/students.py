from sqlmodel import Field, SQLModel, Relationship
from uuid import uuid4, UUID
from typing import Optional
from datetime import date

from models.teachers import TeacherCreate, Teacher
from models.classroom import Classroom
from models.users import User


class UserForStudent(SQLModel):
    id: UUID
    email: str


class ClassForStudent(SQLModel):
    id: UUID
    name: str
    teacher_id: Optional[UUID]


class StudentCreate(SQLModel):
    name: str = Field(index=True)
    age: Optional[int] = Field(default=None, index=True)
    contact: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    FatherName: Optional[str] = Field(default=None)
    MotherName: Optional[str] = Field(default=None)
    FatherContact: Optional[str] = Field(default=None)
    MotherContact: Optional[str] = Field(default=None)
    notification_token: Optional[str] = Field(default=None)
    class_id: Optional[UUID] = Field(default=None, foreign_key="classrooms.id")
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", unique=True)
    
    # New fields
    roll_number: Optional[int] = Field(default=None, index=True)
    date_of_birth: Optional[date] = Field(default=None)


class Student(StudentCreate, table=True):
    __tablename__ = "students"
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    
    classroom: "Classroom" = Relationship(back_populates="students")
    user: User = Relationship(back_populates="student_profile")


class StudentRead(SQLModel):
    id: UUID
    name: str
    age: Optional[int]
    contact: Optional[str]
    address: Optional[str]
    class_id: Optional[UUID]
    user: Optional[UserForStudent]
    FatherName: Optional[str]
    MotherName: Optional[str]
    FatherContact: Optional[str]
    MotherContact: Optional[str]
    notification_token: Optional[str]
    classroom: Optional[ClassForStudent]

    # Include the new fields
    roll_number: Optional[int]
    date_of_birth: Optional[date]
