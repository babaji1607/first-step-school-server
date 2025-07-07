from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import date, datetime
from typing import Optional, List

class DiaryBase(SQLModel):
    title: str
    description: Optional[str] = None
    classname: str
    file_url: Optional[str] = None

class DiaryItem(DiaryBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    creation_date: date = Field(default_factory=date.today)

class DiaryCreate(DiaryBase):
    pass

class DiaryUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    classname: Optional[str] = None
    file_url: Optional[str] = None

class DiaryRead(DiaryBase):
    id: UUID
    creation_date: date

class DiaryPaginationResponse(SQLModel):
    total: int
    offset: int
    limit: int
    items: List[DiaryRead]
