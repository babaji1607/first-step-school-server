# routers/students.py
from fastapi import APIRouter, HTTPException, status, Query, Depends
from models.students import Student, StudentCreate, StudentRead
from database import SessionDep
from typing import Annotated, List
from sqlmodel import select
from uuid import UUID
from Utilities.auth import require_min_role


router = APIRouter(
    prefix="/students",
    tags=["students"],
    dependencies=[Depends(require_min_role("student"))],
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
def create_student(student_data: StudentCreate, session: SessionDep) -> Student:
    # Check for existing student with same unique identity details
    stmt = select(Student).where(
        Student.name == student_data.name,
        Student.age == student_data.age,
        Student.contact == student_data.contact,
        Student.class_id == student_data.class_id,
    )
    existing_student = session.exec(stmt).first()

    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student with the same details already exists"
        )

    # Create and persist the new student
    new_student = Student.model_validate(student_data)
    session.add(new_student)
    session.commit()
    session.refresh(new_student)
    return new_student



@router.get("/showall/", response_model=list[StudentRead])
def read_students(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
    user = Depends(require_min_role("admin"))
) -> list[Student]:
    students = session.exec(select(Student).offset(offset).limit(limit)).all()
    return students


@router.get("/student/{student_id}/", response_model=StudentRead)
def read_student(student_id: UUID, session: SessionDep) -> Student:
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {student_id} not found"
        ) # here f is a f-string, which is a way to format strings in Python 
    return stud



@router.delete("/student/{student_id}")
def delete_student(student_id: UUID, session: SessionDep):
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(stud)
    session.commit()
    return {"ok": True, "deleted_student_id": student_id}


# be carefule with trailing slashes in frontend
@router.put("/student/{student_id}/", response_model=Student)
def update_student(
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

    # Apply full update
    updated_fields = updated_data.dict()
    for field, value in updated_fields.items():
        setattr(student, field, value)

    session.add(student)
    session.commit()
    session.refresh(student)

    return student
