from sqlmodel import Field, SQLModel, Relationship
from uuid import uuid4, UUID
from models.teachers import TeacherCreate, Teacher
from models.classroom import Classroom
from models.users import User

class UserForStudent(SQLModel):
    id: UUID
    email: str
    
class ClassForStudent(SQLModel):
    id: UUID
    name: str
    teacher_id: UUID
    



# SQlMOdel serves as both basemodel and a table model
# damn thats a good idea 

class StudentCreate(SQLModel):
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    contact: str | None = Field(default=None)
    address: str | None = Field(default=None)
    FatherName: str | None = Field(default=None)
    MotherName: str | None = Field(default=None)
    FatherContact: str | None = Field(default=None)
    MotherContact: str | None = Field(default=None)
    notification_token: str | None = Field(default=None)
    class_id: UUID | None = Field(default=None, foreign_key="classrooms.id")
    user_id: UUID | None = Field(default=None, foreign_key="users.id", unique=True)

class Student(StudentCreate, table=True):
    __tablename__ = "students"
    id: UUID | None = Field(default_factory=uuid4, primary_key=True)    
    classroom: "Classroom" = Relationship(back_populates="students")
    user: User = Relationship(back_populates="student_profile")
    
    
    
class StudentRead(SQLModel):  # I need to create this model so that I can show parents array
    id: UUID
    name: str
    age: int | None
    contact: str | None
    address: str | None
    class_id: UUID | None
    user: UserForStudent | None
    FatherName: str | None
    MotherName: str | None
    FatherContact: str | None
    MotherContact: str | None
    notification_token: str | None
    classroom: ClassForStudent | None



    
    
