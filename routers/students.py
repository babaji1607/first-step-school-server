# routers/students.py
from fastapi import APIRouter, HTTPException, status, Query
from models.students import Student
from database import SessionDep
from typing import Annotated
from sqlmodel import select

router = APIRouter(
    prefix="/students",
    tags=["students"]
)

# @router.post("/", status_code=status.HTTP_201_CREATED, response_model=Student)
# async def create_student(student: Student):
   
#     return student



@router.post("/create/", status_code=status.HTTP_201_CREATED, response_model=Student)
def create_hero(student: Student, session: SessionDep) -> Student:
    session.add(student)
    session.commit()
    session.refresh(student)
    return student


@router.get("/showall/")
def read_students(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Student]:
    heroes = session.exec(select(Student).offset(offset).limit(limit)).all()
    return heroes


@router.get("/student/{student_id}/", response_model=Student)
def read_student(student_id: int, session: SessionDep) -> Student:
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Student not found")
    return stud



@router.delete("/student/{student_id}")
def delete_student(student_id: int, session: SessionDep):
    stud = session.get(Student, student_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(stud)
    session.commit()
    return {"ok": True, "deleted_student_id": student_id}