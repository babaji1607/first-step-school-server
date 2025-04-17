from sqlmodel import Field, SQLModel, Relationship
from uuid import uuid4, UUID



# SQlMOdel serves as both basemodel and a table model
# damn thats a good idea 

class StudentCreate(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    Class : str | None = Field(default=None)
    contact: str | None = Field(default=None)
    address: str | None = Field(default=None)
    parent_id: UUID | None = Field(default=None, foreign_key="parents.id")

class Student(StudentCreate, table=True):
    __tablename__ = "students"
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)    
    parent:'Parent'  = Relationship(back_populates="students")
    