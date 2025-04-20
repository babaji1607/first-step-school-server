# Now let's update the router with separate endpoints
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from Utilities.auth import require_min_role

from models.notifications import Notification, NotificationCreate, NotificationRead, RecipientType
from database import SessionDep

router = APIRouter(
    prefix="/notifications", 
    tags=["Notifications"],
    dependencies=[Depends(require_min_role("student"))],
)

@router.post("/", response_model=NotificationRead)
def create_notification(   
    notification: NotificationCreate,
    session: SessionDep,
):
    new_notification = Notification.from_orm(notification)
    session.add(new_notification)
    session.commit()
    session.refresh(new_notification)
    return new_notification

# Teacher-specific endpoints
@router.get("/teachers", response_model=List[NotificationRead])
def get_teacher_notifications(
    session: SessionDep,
    teacher_id: Optional[UUID] = None,
):
    query = select(Notification).where(
        (Notification.recipient_type.in_([
            RecipientType.TEACHER, 
            RecipientType.TEACHERGLOBAL, 
            RecipientType.GLOBAL
        ]))
    )

    if teacher_id:
        query = query.where(
            (Notification.recipient_id == teacher_id) | 
            (Notification.recipient_id == None)
        )
    
    notifications = session.exec(query).all()
    return notifications


# Student-specific endpoints
@router.get("/students", response_model=List[NotificationRead])
def get_student_notifications(
    session: SessionDep,
    student_id: Optional[UUID] = None,
):
    query = select(Notification).where(
        (Notification.recipient_type.in_([
            RecipientType.STUDENT, 
            RecipientType.STUDENTGLOBAL, 
            RecipientType.GLOBAL
        ]))
    )

    if student_id:
        query = query.where(
            (Notification.recipient_id == student_id) | 
            (Notification.recipient_id == None)
        )
    
    notifications = session.exec(query).all()
    return notifications

# Global notifications endpoint (original functionality)
@router.get("/all", response_model=List[NotificationRead])
def get_all_global_notifications(
    session: SessionDep,
):
    query = select(Notification)
    # .where(Notification.recipient_type == RecipientType.GLOBAL)
    notifications = session.exec(query).all()
    return notifications

# Mark notification as read
@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_as_read(
    notification_id: UUID,
    session: SessionDep,
):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: UUID,   
    session: SessionDep,
):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    session.delete(notification)
    session.commit()
    return {"ok": True}