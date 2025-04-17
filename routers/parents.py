from fastapi import APIRouter, HTTPException, status, Query
from database import SessionDep
from typing import Annotated
from sqlmodel import select
from models.parents import Parent, ParentCreate, ParentRead


router = APIRouter(
    prefix="/parents",
    tags=["parents"]
)

@router.post("/create/", status_code=status.HTTP_201_CREATED, response_model=Parent)
def create_hero(parent: ParentCreate, session: SessionDep) -> Parent:
    db_parent = Parent(**parent.dict())  # ✅ create SQLModel from Pydantic data
    session.add(db_parent)
    session.commit()
    session.refresh(db_parent)
    return db_parent

@router.get("/show_all", response_model=list[ParentRead], status_code=status.HTTP_200_OK)
def get_all_parents(session: SessionDep) -> list[Parent]:
    statement = select(Parent)
    parents = session.exec(statement).all()
    return parents