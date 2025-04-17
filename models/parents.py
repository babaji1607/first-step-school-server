from sqlmodel import SQLModel, Field, Relationship
from uuid import uuid4, UUID


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
    students: list['Student'] = Relationship(back_populates="parent") # this name will be name of field not the name of table
    