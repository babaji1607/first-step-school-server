from typing import Annotated
from uuid import uuid4, UUID
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, SQLModel, Relationship


class StudentForTeacher(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    class_name : str | None = Field(default=None)
    contact: str | None = Field(default=None)
    address: str | None = Field(default=None)
    

class TeacherCreate(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    contact: str | None = Field(default=None)
    subject: str | None = Field(default=None)
    assignedClass: str | None = Field(default=None)
    address: str | None = Field(default=None)  
    
class Teacher(TeacherCreate, table=True):
    __tablename__ = "teachers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)   
    students: list['Student'] = Relationship(back_populates="class_teacher", sa_relationship_kwargs={"cascade": "all, delete"}) # this name will be name of field not the name of table
    
class TeacherRead(SQLModel):  # I need to create this model so that I can show parents array
    id: UUID
    name: str
    age: int | None
    contact: str | None
    subject: str | None
    assignedClass: str | None
    address: str | None  
    students: list[StudentForTeacher] | None  # this needs to be mentioned specifically