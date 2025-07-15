from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import select
from uuid import UUID
from typing import List
from database import SessionDep
from Utilities.auth import require_min_role
from services.feepost.models import FeePost, FeePostCreate, FeePostRead, FeePostPaginationResponse, FeePostUpdateStatus
# from routers.fee_recipt import create_fee_receipt

fee_router = APIRouter(
    prefix="/feepost",
    tags=["FeePost"],
    dependencies=[Depends(require_min_role("student"))]
)



@fee_router.post("/", response_model=FeePostRead, dependencies=[Depends(require_min_role("admin"))])
def create_fee_post(session: SessionDep, payload: FeePostCreate):
    fee_post = FeePost(**payload.model_dump())
    session.add(fee_post)
    session.commit()
    session.refresh(fee_post)
    return fee_post

@fee_router.delete("/{fee_id}", dependencies=[Depends(require_min_role("admin"))])
def delete_fee_post(fee_id: UUID, session: SessionDep):
    fee_post = session.get(FeePost, fee_id)
    if not fee_post:
        raise HTTPException(status_code=404, detail="Fee post not found")
    session.delete(fee_post)
    session.commit()
    return {"ok": True}

@fee_router.get("/", response_model=FeePostPaginationResponse)
def get_all_fee_posts(session: SessionDep, offset: int = Query(0, ge=0), limit: int = Query(10, le=100)):
    total_items = session.exec(select(FeePost)).all()
    paginated_items = session.exec(
        select(FeePost)
        .order_by(FeePost.creation_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "total": len(total_items),
        "offset": offset,
        "limit": limit,
        "items": paginated_items,
    }

@fee_router.get("/by-student", response_model=FeePostPaginationResponse)
def get_fee_posts_by_student(
    session: SessionDep,
    student_id: UUID = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
):
    total_items = session.exec(
        select(FeePost).where(FeePost.student_id == student_id)
    ).all()

    paginated_items = session.exec(
        select(FeePost)
        .where(FeePost.student_id == student_id)
        .order_by(FeePost.creation_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return FeePostPaginationResponse(
        total=len(total_items),
        offset=offset,
        limit=limit,
        items=paginated_items
    )



@fee_router.patch("/{fee_id}/status", response_model=FeePostRead, dependencies=[Depends(require_min_role("admin"))])
def update_fee_post_status(
    fee_id: UUID,
    payload: FeePostUpdateStatus,
    session: SessionDep
):
    fee_post = session.get(FeePost, fee_id)
    if not fee_post:
        raise HTTPException(status_code=404, detail="Fee post not found")

    fee_post.mode = payload.mode
    fee_post.is_paid = payload.is_paid

    session.add(fee_post)
    session.commit()
    session.refresh(fee_post)
    return fee_post