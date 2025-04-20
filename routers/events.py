from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from models.events import Event, EventCreate, EventRead, EventStatus
from Utilities.auth import require_min_role
from database import SessionDep


router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=[Depends(require_min_role("student"))],  # Update role as needed
)

# Create a new event
@router.post("/", response_model=EventRead)
def create_event(event: EventCreate, session: SessionDep):
    new_event = Event.from_orm(event)
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event

# Get all events for a specific user (Teacher or Student)
@router.get("/", response_model=List[EventRead])
def get_events(
    session: SessionDep,
    user_id: Optional[UUID] = None,
    recipient_type: Optional[str] = None,  # Teacher, Student, Global
):
    query = select(Event)

    # Filter by recipient type and user_id if provided
    if recipient_type:
        query = query.where(Event.recipient_type == recipient_type)
    if user_id:
        query = query.where(Event.recipient_id == user_id)

    events = session.exec(query).all()
    return events

# Get a specific event by ID
@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: UUID, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Update an event's status
@router.patch("/{event_id}/status", response_model=EventRead)
def update_event_status(
    event_id: UUID,
    status: EventStatus,
    session: SessionDep,
):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.status = status
    session.add(event)
    session.commit()
    session.refresh(event)
    return event

# Delete an event
@router.delete("/{event_id}")
def delete_event(event_id: UUID, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    session.delete(event)
    session.commit()
    return {"ok": True}
