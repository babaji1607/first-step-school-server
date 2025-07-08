from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Optional, List

class DiaryBase(SQLModel):
    title: str
    description: Optional[str] = None
    classname: str
    file_url: Optional[str] = None

class DiaryItem(DiaryBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    creation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # ✅ Aware datetime

class DiaryCreate(DiaryBase):
    pass

class DiaryUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    classname: Optional[str] = None
    file_url: Optional[str] = None

class DiaryRead(DiaryBase):
    id: UUID
    creation_date: datetime  # ✅ Use datetime

class DiaryPaginationResponse(SQLModel):
    total: int
    offset: int
    limit: int
    items: List[DiaryRead]
