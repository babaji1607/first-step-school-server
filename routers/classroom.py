from fastapi import APIRouter, HTTPException, status, Query, Depends
from models.classroom import Classroom, ClassroomCreate, ClassroomRead
from database import SessionDep
from typing import List, Optional
from sqlmodel import select
from uuid import UUID
from Utilities.auth import require_min_role

router = APIRouter(
    prefix="/classrooms",
    tags=["classrooms"],
    dependencies=[Depends(require_min_role("teacher"))],
)


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=ClassroomRead)
def create_classroom(classroom: ClassroomCreate, session: SessionDep) -> Classroom:
    # Check if classroom with same name exists (name is unique)
    existing = session.exec(
        select(Classroom).where(Classroom.name == classroom.name)
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Classroom with the same name already exists"
        )

    new_classroom = Classroom(**classroom.dict())
    session.add(new_classroom)
    session.commit()
    session.refresh(new_classroom)
    return new_classroom

@router.get("/names", response_model=List[str])
def get_all_class_names(session: SessionDep) -> List[str]:
    result = session.exec(select(Classroom.name)).all()
    return result

@router.get("/showall", response_model=List[ClassroomRead])
def read_classrooms(
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(100, le=100),
    user = Depends(require_min_role("admin"))
) -> List[Classroom]:
    classrooms = session.exec(select(Classroom).offset(offset).limit(limit)).all()
    return classrooms


@router.get("/search", response_model=dict)
def search_classrooms(
    session: SessionDep,
    name: Optional[str] = None,
    page: int = 1,
    limit: int = 10
):
    if not name:
        raise HTTPException(status_code=400, detail="Provide at least the name for search.")

    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page and limit must be positive integers")

    offset = (page - 1) * limit
    query = select(Classroom)

    if name:
        query = query.where(Classroom.name.ilike(f"%{name}%"))

    total_results = session.exec(query).all()
    total = len(total_results)

    query = query.offset(offset).limit(limit)
    results = session.exec(query).all()

    if not results:
        raise HTTPException(status_code=404, detail="No classrooms found with the given criteria")

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "results": results
    }


@router.get("/classroom/{classroom_id}", response_model=ClassroomRead)
def read_classroom(classroom_id: UUID, session: SessionDep) -> Classroom:
    classroom = session.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom


@router.put("/classroom/{classroom_id}", response_model=ClassroomRead)
def update_classroom(
    classroom_id: UUID,
    updated_data: ClassroomCreate,
    session: SessionDep
) -> Classroom:
    classroom = session.get(Classroom, classroom_id)

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    updated_fields = updated_data.dict()
    for field, value in updated_fields.items():
        setattr(classroom, field, value)

    session.add(classroom)
    session.commit()
    session.refresh(classroom)

    return classroom


@router.delete("/classroom/{classroom_id}")
def delete_classroom(classroom_id: UUID, session: SessionDep):
    classroom = session.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    session.delete(classroom)
    session.commit()
    return {"ok": True, "deleted_classroom_id": classroom_id}


@router.get("/by-teacher/{teacher_id}", response_model=List[ClassroomRead])
def get_classrooms_by_teacher(teacher_id: UUID, session: SessionDep) -> List[Classroom]:
    classrooms = session.exec(
        select(Classroom).where(Classroom.teacher_id == teacher_id)
    ).all()

    if not classrooms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No classrooms found for teacher with ID {teacher_id}"
        )

    return classrooms
