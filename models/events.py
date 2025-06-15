from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

class EventStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class EventBase(SQLModel):
    title: str
    description: str
    event_date: datetime
    imageUrl: str | None = Field(default=None)
    status: EventStatus = Field(default=EventStatus.ACTIVE)

class Event(EventBase, table=True):
    __tablename__ = "events"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EventCreate(EventBase):
    pass

class EventRead(EventBase):
    id: UUID
    created_at: datetime
