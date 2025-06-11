# Updated notification models with class support
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

class RecipientType(str, PyEnum):
    TEACHER = "teacher" 
    STUDENT = "student"  
    TEACHERGLOBAL = "teacher_global"
    STUDENTGLOBAL = "student_global"
    GLOBAL = "global"  # For notifications to all users

class NotificationBase(SQLModel):
    title: str
    message: str
    recipient_type: str = Field(default="global")  # Changed to str to allow dynamic class names
    recipient_id: UUID | None = Field(default=None)
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

class ClassNotificationCreate(SQLModel):
    title: str
    message: str

# Helper function to check if recipient_type is a predefined enum value
def is_predefined_recipient_type(recipient_type: str) -> bool:
    """Check if the recipient_type is one of the predefined enum values"""
    return recipient_type in [e.value for e in RecipientType]

def is_class_name(recipient_type: str) -> bool:
    """Check if the recipient_type is a class name (not a predefined enum value)"""
    return not is_predefined_recipient_type(recipient_type)