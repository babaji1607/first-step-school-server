from sqlmodel import SQLModel, Field, Column, JSON
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, Dict, List
from enum import Enum

class FeeMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"

class FeePostBase(SQLModel):
    student_id: UUID
    title: str
    other_fee: Optional[Dict[str, float]] = Field(
        default=None,
        sa_column=Column(JSON, nullable=True)  # JSONB if PostgreSQL
    )
    deadline: datetime
    is_paid: bool = False
    mode: FeeMode

class FeePost(FeePostBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FeePostCreate(FeePostBase):
    pass

class FeePostRead(FeePostBase):
    id: UUID
    creation_date: datetime

class FeePostPaginationResponse(SQLModel):
    total: int
    offset: int
    limit: int
    items: List[FeePostRead]
