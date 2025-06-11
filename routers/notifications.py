# Updated router with class notifications and student-specific endpoints
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from Utilities.auth import require_min_role, get_current_user  # Assuming you have get_current_user
import os

from models.notifications import (
    Notification, 
    NotificationCreate, 
    NotificationRead, 
    RecipientType,
    ClassNotificationCreate,
    is_predefined_recipient_type,
    is_class_name
)
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
        # If recipient_token is provided, send to token directly
        if notification.recipient_token:
            message = messaging.Message(
                token=notification.recipient_token,
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.message
                )
            )
            messaging.send(message=message)
            print(f"Sent notification to token: {notification.recipient_token[:10]}...")
        else:
            # Fallback to topic-based notification
            topic = notification.recipient_type
            
            # If it's a class name (not predefined enum), use class_ prefix for Firebase topic
            if is_class_name(notification.recipient_type):
                topic = f"class_{notification.recipient_type}"
            
            message = messaging.Message(
                topic=topic,
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.message
                )
            )
            messaging.send(message=message)
            print(f"Sent notification to topic: {topic}")
            
    except Exception as e:
        print(f"Failed to send Firebase notification: {e}")
        # Don't fail the entire request if notification sending fails
    
    return new_notification

# NEW: Class-specific notification endpoint
@router.post("/class/{class_name}", response_model=NotificationRead)
def create_class_notification(
    class_name: str,
    notification: ClassNotificationCreate,
    session: SessionDep,
):
    """Send notification to a specific class"""
    new_notification = Notification(
        title=notification.title,
        message=notification.message,
        recipient_type=class_name  # Use class name directly as recipient_type
    )
    
    session.add(new_notification)
    session.commit()
    session.refresh(new_notification)
    
    try:
        # Always send to class topic for this endpoint
        message = messaging.Message(
            topic=f"class_{class_name}",
            notification=messaging.Notification(
                title=notification.title,
                body=notification.message
            )
        )
        messaging.send(message=message)
        print(f"Sent notification to class topic: class_{class_name}")
    except Exception as e:
        print(f"Failed to send Firebase notification to class {class_name}: {e}")
        # Don't fail the entire request if notification sending fails
    
    return new_notification

# NEW: Get notifications for a specific class
@router.get("/class/{class_name}", response_model=List[NotificationRead])
def get_class_notifications(
    class_name: str,
    session: SessionDep,
):
    """Get all notifications for a specific class"""
    query = select(Notification).where(
        Notification.recipient_type == class_name
    )
    
    notifications = session.exec(query).all()
    return notifications

# Teacher-specific endpoints
@router.get("/teachers", response_model=List[NotificationRead])
def get_teacher_notifications(
    session: SessionDep,
    teacher_id: Optional[UUID] = None,
):
    query = select(Notification).where(
        (Notification.recipient_type.in_([
            RecipientType.TEACHER.value, 
            RecipientType.TEACHERGLOBAL.value, 
            RecipientType.GLOBAL.value
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
            RecipientType.STUDENT.value, 
            RecipientType.STUDENTGLOBAL.value, 
            RecipientType.GLOBAL.value
        ]))
    )

    if student_id:
        query = query.where(
            (Notification.recipient_id == student_id) | 
            (Notification.recipient_id == None)
        )
    
    notifications = session.exec(query).all()
    return notifications

# NEW: Get notifications for current student (based on token)
@router.get("/my-notifications", response_model=List[NotificationRead])
def get_my_notifications(
    session: SessionDep,
    current_user = Depends(get_current_user),  # Assuming this returns user info with id and class
):
    """Get all notifications for the current student based on their token"""
    student_id = current_user.id
    student_class = getattr(current_user, 'class_name', None)  # Adjust based on your user model
    
    # Build query for notifications relevant to this student
    conditions = [
        # Global notifications
        Notification.recipient_type == RecipientType.GLOBAL.value,
        # Student global notifications
        Notification.recipient_type == RecipientType.STUDENTGLOBAL.value,
        # Student-specific notifications
        (Notification.recipient_type == RecipientType.STUDENT.value) & 
        (Notification.recipient_id == student_id)
    ]
    
    # Add class-specific notifications if student has a class
    if student_class:
        conditions.append(Notification.recipient_type == student_class)
    
    # Combine conditions with OR
    from sqlmodel import or_
    query = select(Notification).where(or_(*conditions))
    
    notifications = session.exec(query).all()
    return notifications

# Alternative: Get notifications for specific student ID
@router.get("/student/{student_id}", response_model=List[NotificationRead])
def get_notifications_for_student(
    student_id: UUID,
    session: SessionDep,
    student_class: Optional[str] = Query(None, description="Student's class name"),
):
    """Get all notifications for a specific student by ID"""
    # Build query for notifications relevant to this student
    conditions = [
        # Global notifications
        Notification.recipient_type == RecipientType.GLOBAL.value,
        # Student global notifications
        Notification.recipient_type == RecipientType.STUDENTGLOBAL.value,
        # Student-specific notifications
        (Notification.recipient_type == RecipientType.STUDENT.value) & 
        (Notification.recipient_id == student_id)
    ]
    
    # Add class-specific notifications if class is provided
    if student_class:
        conditions.append(Notification.recipient_type == student_class)
    
    # Combine conditions with OR
    from sqlmodel import or_
    query = select(Notification).where(or_(*conditions))
    
    notifications = session.exec(query).all()
    return notifications

# Global notifications endpoint (original functionality)
@router.get("/all", response_model=List[NotificationRead])
def get_all_global_notifications(
    session: SessionDep,
):
    query = select(Notification)
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