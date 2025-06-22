from fastapi import APIRouter, HTTPException, status, Query, Depends
from models.students import Student, StudentCreate, StudentRead
from database import SessionDep
from typing import Annotated, List
from sqlmodel import select
from uuid import UUID
from datetime import date
from Utilities.auth import require_min_role

router = APIRouter(
    prefix="/students",
    tags=["students"],
    dependencies=[Depends(require_min_role("student"))],
)

@router.get("/search/", response_model=dict)
def search_students(
    session: SessionDep,
    id: UUID | None = None,
    name: str | None = None,
    age: int | None = None,
    roll_number: int | None = None,
    date_of_birth: date | None = None,
    page: int = 1,
    limit: int = 10,
):
    # Prevent search without criteria
    if all(param is None for param in [id, name, age, roll_number, date_of_birth]):
        raise HTTPException(
            status_code=400,
            detail="At least one of 'id', 'name', 'age', 'roll_number', or 'date_of_birth' must be provided"
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
    if roll_number is not None:
        query = query.where(Student.roll_number == roll_number)
    if date_of_birth is not None:
        query = query.where(Student.date_of_birth == date_of_birth)

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
    # Optional: check for existing student by roll_number within class
    if student_data.roll_number and student_data.class_id:
        stmt = select(Student).where(
            Student.roll_number == student_data.roll_number,
            Student.class_id == student_data.class_id
        )
        existing = session.exec(stmt).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student with the same roll number already exists in this class"
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
        )
    return stud


@router.delete("/student/{student_id}")
def delete_student(student_id: UUID, session: SessionDep):
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(stud)
    session.commit()
    return {"ok": True, "deleted_student_id": student_id}


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

    updated_fields = updated_data.dict(exclude_unset=True)
    for field, value in updated_fields.items():
        setattr(student, field, value)

    session.add(student)
    session.commit()
    session.refresh(student)

    return student
