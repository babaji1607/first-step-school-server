from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import SQLModel, Field


class FeeReceiptBase(SQLModel):
    student_id: UUID
    total_amount: float
    paid_on: datetime = Field(default_factory=datetime.utcnow)
    payment_reference: Optional[str] = None  # Reference from third-party gateway
    remarks: Optional[str] = None


class FeeReceipt(FeeReceiptBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)


class FeeReceiptCreate(FeeReceiptBase):
    pass


class FeeReceiptRead(FeeReceiptBase):
    id: UUID
