from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlmodel import select
from typing import List
from uuid import UUID

from models.fee_receipt import FeeReceipt, FeeReceiptCreate, FeeReceiptRead
from database import SessionDep
from Utilities.auth import require_min_role

router = APIRouter(
    prefix="/fee-receipts",
    tags=["fee-receipts"],
    dependencies=[Depends(require_min_role("teacher"))],
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FeeReceiptRead)
def create_fee_receipt(
    receipt_data: FeeReceiptCreate, session: SessionDep
):
    new_receipt = FeeReceipt.from_orm(receipt_data)
    session.add(new_receipt)
    session.commit()
    session.refresh(new_receipt)
    return new_receipt


@router.get("/", response_model=List[FeeReceiptRead])
def get_all_fee_receipts(
    session: SessionDep,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
):
    offset = (page - 1) * limit
    receipts = session.exec(select(FeeReceipt).offset(offset).limit(limit)).all()
    return receipts

@router.get("/{receipt_id}", response_model=FeeReceiptRead)
def get_fee_receipt(receipt_id: UUID, session: SessionDep):
    receipt = session.get(FeeReceipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt



@router.get("/student/{student_id}", response_model=List[FeeReceiptRead])
def get_fee_receipts_by_student(
    session: SessionDep,
    student_id: UUID = Path(..., description="Student ID to fetch fee receipts for"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=100),
):
    offset = (page - 1) * limit
    query = select(FeeReceipt).where(FeeReceipt.student_id == student_id)
    query = query.offset(offset).limit(limit)

    receipts = session.exec(query).all()

    if not receipts:
        raise HTTPException(status_code=404, detail="No receipts found for the student")

    return receipts
