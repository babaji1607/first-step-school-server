# Simplified router with generic recipient_type and recipient_id endpoints
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from Utilities.auth import require_min_role, get_current_user
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
                topic = f"{notification.recipient_type}"
            
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

# Get notifications by recipient_type
@router.get("/by-type/{recipient_type}", response_model=List[NotificationRead])
def get_notifications_by_recipient_type(
    recipient_type: str,
    session: SessionDep,
):
    """Get all notifications for a specific recipient type (e.g., 'global', 'student', 'teacher', 'class_name')"""
    query = select(Notification).where(
        Notification.recipient_type == recipient_type
    )
    
    notifications = session.exec(query).all()
    return notifications

# Get notifications by recipient_id
@router.get("/by-id/{recipient_id}", response_model=List[NotificationRead])
def get_notifications_by_recipient_id(
    recipient_id: UUID,
    session: SessionDep,
):
    """Get all notifications for a specific recipient ID"""
    query = select(Notification).where(
        Notification.recipient_id == recipient_id
    )
    
    notifications = session.exec(query).all()
    return notifications

# Get all notifications (for admin purposes)
@router.get("/all", response_model=List[NotificationRead])
def get_all_notifications(
    session: SessionDep,
):
    """Get all notifications"""
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