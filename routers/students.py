# routers/students.py
from fastapi import APIRouter, HTTPException, status, Query
from models.students import Student, StudentCreate
from database import SessionDep
from typing import Annotated
from sqlmodel import select
from uuid import UUID


router = APIRouter(
    prefix="/students",
    tags=["students"]
)

# @router.post("/", status_code=status.HTTP_201_CREATED, response_model=Student)
# async def create_student(student: Student):
   
#     return student

@router.get("/search/", response_model=dict)
def search_students(
    session: SessionDep,
    id: int | None = None,
    name: str | None = None,
    age: int | None = None,
    page: int = 1,
    limit: int = 10,
):
    # Prevent search without criteria
    if id is None and name is None and age is None:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'id', 'name', or 'age' must be provided"
        )

    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page and limit must be positive integers")

    offset = (page - 1) * limit

    query = select(Student)

    if id is not None:
        query = query.where(Student.id == id)
    if name is not None:
        query = query.where(Student.name.ilike(f"%{name}%"))
    if age is not None:
        query = query.where(Student.age == age)

    total_query = session.exec(query).all()
    total_count = len(total_query)

    query = query.offset(offset).limit(limit)
    results = session.exec(query).all()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No students found with the given criteria"
        )

    return {
        "page": page,
        "limit": limit,
        "total": total_count,
        "results": results
    }



@router.post("/create/", status_code=status.HTTP_201_CREATED, response_model=Student)
def create_student(student: StudentCreate, session: SessionDep) -> Student:
    # Check for existing student based on name, age, class, etc.
    existing_student = session.exec(
        select(Student).where(
            Student.name == student.name,
            Student.age == student.age,
            Student.Class == student.Class,
            Student.contact == student.contact,
        )
    ).first()

    if existing_student:
        raise HTTPException(
            status_code=409,
            detail="Student with the same details already exists"
        )

    new_student = Student(**student.dict())
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    return new_student



@router.get("/showall/", response_model=list[Student])
def read_students(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Student]:
    students = session.exec(select(Student).offset(offset).limit(limit)).all()
    return students


@router.get("/student/{student_id}/", response_model=Student)
def read_student(student_id: int, session: SessionDep) -> Student:
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        ) # here f is a f-string, which is a way to format strings in Python 
    return stud



@router.delete("/student/{student_id}")
def delete_student(student_id: int, session: SessionDep):
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(stud)
    session.commit()
    return {"ok": True, "deleted_student_id": student_id}


@router.patch("/student/{student_id}/", response_model=Student)
def patch_student(
    student_id: UUID,
    updated_data: StudentCreate,
    session: SessionDep
) -> Student:
    student = session.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        )

    # Apply partial updates
    update_fields = updated_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(student, field, value)

    session.add(student)
    session.commit()
    session.refresh(student)

    return student