from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlmodel import Session, select
from typing import List, Optional
from uuid import UUID
from models.events import Event, EventCreate, EventRead, EventStatus
from Utilities.auth import require_min_role
from database import SessionDep
from Utilities.s3bucketupload import upload_to_s3
from datetime import datetime

router = APIRouter(
    prefix="/events",
    tags=["Events"],
    dependencies=[Depends(require_min_role("student"))],
)

@router.post("/", response_model=EventRead)
async def create_event(
    session: SessionDep,
    title: str = Form(...),
    description: str = Form(...),
    event_date: datetime = Form(...), 
    image: UploadFile = File(None),
):
    image_url = None
    if image:
        try:
            image_url = upload_to_s3(image)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

    event_data = EventCreate(
        title=title,
        description=description,
        imageUrl=image_url,
         event_date=event_date,
    )

    new_event = Event.from_orm(event_data)
    session.add(new_event)
    session.commit()
    session.refresh(new_event)
    return new_event


@router.get("/", response_model=List[EventRead])
def get_events(
    session: SessionDep,
    user_id: Optional[UUID] = None,
    recipient_type: Optional[str] = None,
):
    query = select(Event)
    if recipient_type:
        query = query.where(Event.recipient_type == recipient_type)
    if user_id:
        query = query.where(Event.recipient_id == user_id)

    return session.exec(query).all()


@router.get("/{event_id}", response_model=EventRead)
def get_event(event_id: UUID, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


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


@router.delete("/{event_id}")
def delete_event(event_id: UUID, session: SessionDep):
    event = session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    session.delete(event)
    session.commit()
    return {"ok": True}
