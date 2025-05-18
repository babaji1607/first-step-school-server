from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from uuid import uuid4, UUID
from models.teachers import TeacherCreate, StudentForTeacher

class StudentForClassroom(SQLModel):
    id: UUID
    name: str
    age: int | None = None
    contact: str | None = None
    address: str | None = None

class ClassroomBase(SQLModel):
    name: str = Field(index=True, unique=True)  # e.g., "10A", "5B"
    teacher_id: UUID | None = Field(default=None, foreign_key="teachers.id")


class Classroom(ClassroomBase, table=True):
    __tablename__ = "classrooms"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    teacher: "Teacher" = Relationship(back_populates="classroom")
    students: List["Student"] = Relationship(back_populates="classroom")


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomRead(ClassroomBase):
    id: UUID
    teacher: Optional[TeacherCreate] = None
    students: List[StudentForClassroom] = []
    
    
Classroom.model_rebuild()