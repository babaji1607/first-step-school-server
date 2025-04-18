from fastapi import APIRouter, HTTPException, status
from database import SessionDep
from typing import List
from sqlmodel import select
from uuid import UUID

from models.parents import Parent, ParentCreate, ParentRead, ParentUpdate

router = APIRouter(
    prefix="/parents",
    tags=["parents"]
)

# CREATE
@router.post("/create/", status_code=status.HTTP_201_CREATED, response_model=ParentRead)
def create_parent(parent: ParentCreate, session: SessionDep) -> Parent:
    db_parent = Parent(**parent.dict())
    session.add(db_parent)
    session.commit()
    session.refresh(db_parent)
    return db_parent

# READ
@router.get("/show_all", response_model=List[ParentRead], status_code=status.HTTP_200_OK)
def get_all_parents(session: SessionDep) -> List[Parent]:
    statement = select(Parent)
    parents = session.exec(statement).all()
    return parents

# PATCH
@router.patch("/{parent_id}", response_model=ParentRead)
def update_parent(parent_id: UUID, parent_update: ParentUpdate, session: SessionDep):
    parent = session.get(Parent, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    update_data = parent_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(parent, key, value)

    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent

# DELETE
@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent(parent_id: UUID, session: SessionDep):
    parent = session.get(Parent, parent_id)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    session.delete(parent)
    session.commit()
