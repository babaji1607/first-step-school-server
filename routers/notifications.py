# Now let's update the router with separate endpoints
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from Utilities.auth import require_min_role
import os

from models.notifications import Notification, NotificationCreate, NotificationRead, RecipientType
from database import SessionDep
import firebase_admin 
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:  # Check if Firebase is already initialized
        try:
            # On Render, secret files are mounted to /etc/secrets/
            render_secret_path = "/etc/secrets/firststep-school-firebase-adminsdk-fbsvc-538e257346.json"
            local_dev_path = "./firststep-school-firebase-adminsdk-fbsvc-538e257346.json"
            
            # Try Render secret file path first (for production)
            if os.path.exists(render_secret_path):
                creds = credentials.Certificate(render_secret_path)
                print("Using Firebase credentials from Render secret file")
            elif os.path.exists(local_dev_path):
                # Fallback to local file (for development)
                creds = credentials.Certificate(local_dev_path)
                print("Using Firebase credentials from local file")
            else:
                raise FileNotFoundError("Firebase credentials file not found in either location")
            
            firebase_admin.initialize_app(creds)
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            raise e

# Initialize Firebase when module is imported
initialize_firebase()

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
    
    try:
        message = messaging.Message(
            topic=notification.recipient_type,
            notification=messaging.Notification(
                title=notification.title,
                body=notification.message
            )
        )
        messaging.send(message=message)
    except Exception as e:
        print(f"Failed to send Firebase notification: {e}")
        # Don't fail the entire request if notification sending fails
    
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