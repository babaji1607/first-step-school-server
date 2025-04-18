from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4, UUID
from  typing import List
from typing import Optional
from sqlmodel import SQLModel


 # SQlMOdel serves as both basemodel and a table model    ]
class ParentCreate(SQLModel):
      FatherName: str = Field(index=True)
      MotherName: str = Field(index=True)
      PhoneNumber: str | None = Field(default=None)
      Address: str | None = Field(default=None)
      Occupation: str | None = Field(default=None)
      Email: str | None = Field(default=None)
      
      
 
class Parent(ParentCreate, table=True):
    __tablename__ = "parents"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    students: list['Student'] = Relationship(back_populates="parent",  sa_relationship_kwargs={"cascade": "all, delete"}) # this name will be name of field not the name of table



class StudentSchmeaParent(SQLModel): # it should be here instead of models/students.py 
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    class_name : str | None = Field(default=None)
    contact: str | None = Field(default=None)
    address: str | None = Field(default=None)

class ParentRead(SQLModel): # additional model to show students array in the responseJ
    id: UUID
    FatherName: str
    MotherName: str
    PhoneNumber: str | None
    Address: str | None
    Occupation: str | None
    Email: str | None
    students: list[StudentSchmeaParent] | None  # this needs to be mentioned specifically
    

# this fucking circular Imports problem

class ParentUpdate(SQLModel):
    FatherName: Optional[str] = None
    MotherName: Optional[str] = None
    PhoneNumber: Optional[str] = None
    Address: Optional[str] = None
    Occupation: Optional[str] = None
    Email: Optional[str] = None