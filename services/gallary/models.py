from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone


class GalleryItemBase(SQLModel):
    imageUrl: Optional[str] = None
    videoUrl: Optional[str] = None


class GalleryItem(GalleryItemBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GalleryItemCreate(GalleryItemBase):
    pass


class GalleryItemUpdate(GalleryItemBase):
    pass


class GalleryItemRead(GalleryItemBase):
    id: UUID
    date: datetime
