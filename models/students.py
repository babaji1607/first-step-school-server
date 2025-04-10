from sqlmodel import Field, SQLModel

# SQlMOdel serves as both basemodel and a table model
# damn thats a good idea 

class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    Class : str | None = Field(default=None)
    contact: str | None = Field(default=None)
    
    