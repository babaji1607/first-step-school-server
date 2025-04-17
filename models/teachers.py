from typing import Annotated
from uuid import uuid4, UUID
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Teacher(SQLModel, table=True):
    __tablename__ = "teachers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    contact: str | None = Field(default=None)
    subject: str | None = Field(default=None)
    assignedClass: str | None = Field(default=None)
    address: str | None = Field(default=None)    
    