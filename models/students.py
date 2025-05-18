from sqlmodel import Field, SQLModel, Relationship
from uuid import uuid4, UUID
from models.parents import Parent,ParentRead,ParentCreate
from models.teachers import TeacherCreate, Teacher
from models.classroom import Classroom
from models.users import User

class UserForStudent(SQLModel):
    id: UUID
    email: str
    



# SQlMOdel serves as both basemodel and a table model
# damn thats a good idea 

class StudentCreate(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    contact: str | None = Field(default=None)
    address: str | None = Field(default=None)
    parent_id: UUID | None = Field(default=None, foreign_key="parents.id")
    class_id: UUID | None = Field(default=None, foreign_key="classrooms.id")
    user_id: UUID | None = Field(default=None, foreign_key="users.id", unique=True)

class Student(StudentCreate, table=True):
    __tablename__ = "students"
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)    
    parent:Parent  = Relationship(back_populates="students")
    classroom: "Classroom" = Relationship(back_populates="students")
    user: User = Relationship(back_populates="student_profile")
    
    
    
class StudentRead(SQLModel):  # I need to create this model so that I can show parents array
    id: UUID
    name: str
    age: int | None
    contact: str | None
    address: str | None
    parent_id: UUID | None
    class_id: UUID | None
    parent: ParentCreate | None    # this needs to be mentioned specifically
    user: UserForStudent | None



    
    
