# First, let's update the notification models
from sqlmodel import SQLModel, Field, Enum
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

class RecipientType(str, PyEnum):
    TEACHER = "teacher" # no need cuz token will be enough to identify teacher
    STUDENT = "student"  # no need cuz token will be enough to identify student
    TEACHERGLOBAL = "teacher_global"
    STUDENTGLOBAL = "student_global"
    GLOBAL = "global"  # For notifications to all users


## if you want to be class specific then you can add it here
class NotificationBase(SQLModel):
    title: str
    message: str
    recipient_type: RecipientType = Field(default=RecipientType.GLOBAL)
    recipient_token: str | None = Field(default=None)


class Notification(NotificationBase, table=True):
    __tablename__ = "notifications"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NotificationCreate(NotificationBase):
    pass

class NotificationRead(NotificationBase):
    id: UUID
    is_read: bool
    created_at: datetime