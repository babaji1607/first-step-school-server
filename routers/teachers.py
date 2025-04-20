# routers/students.py
from fastapi import APIRouter, HTTPException, status, Query, Depends
from models.teachers import Teacher, TeacherRead, TeacherCreate
from database import SessionDep
from typing import Annotated
from sqlmodel import select
from Utilities.auth import require_min_role

router = APIRouter(
    prefix="/teachers",
    tags=["teachers"],
    dependencies=[Depends(require_min_role("admin"))],
)




@router.post("/create/", status_code=status.HTTP_201_CREATED, response_model=Teacher)
def create_hero(teacher: TeacherCreate, session: SessionDep) -> Teacher:
    db_teacher = Teacher(**teacher.dict())  # ✅ convert to table-mapped model
    session.add(db_teacher)
    session.commit()
    session.refresh(db_teacher)
    return db_teacher



@router.get("/showall/")
def read_students(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[TeacherRead]:
    heroes = session.exec(select(Teacher).offset(offset).limit(limit)).all()
    return heroes


@router.get("/teacher/{teacher_id}/", response_model=Teacher)
def read_student(teacher_id: int, session: SessionDep) -> Teacher:
    stud = session.get(Teacher, teacher_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return stud



@router.delete("/teacher/{teacher_id}")
def delete_student(teacher_id: int, session: SessionDep):
    stud = session.get(Teacher, teacher_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Teacher not found")
    session.delete(stud)
    session.commit()
    return {"ok": True, "deleted_student_id": teacher_id}


@router.put("/teacher/{teacher_id}", response_model=Teacher)
def update_student(teacher_id: int, teacher: Teacher, session: SessionDep):
    stud = session.get(Teacher, teacher_id)
    if not stud:
        raise HTTPException(status_code=404, detail="Teacher not found")
    teacher.id = teacher_id
    session.add(teacher)
    session.commit()
    session.refresh(teacher)
    return teacher