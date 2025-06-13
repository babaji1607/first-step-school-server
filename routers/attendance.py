from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from uuid import UUID

from models.attendance import (
    AttendanceSession,
    AttendanceSessionCreate,
    AttendanceSessionRead,
    AttendanceRecord,
    AttendanceRecordRead,
    AttendanceRecordUpdate,
    StudentMonthlyAttendanceEntry
)
from database import SessionDep
from Utilities.auth import require_min_role

router = APIRouter(
    prefix="/attendance",
    tags=["attendance"],
    dependencies=[Depends(require_min_role("student"))]
)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AttendanceSessionRead)
def create_attendance_session(session_data: AttendanceSessionCreate, session: SessionDep):
    new_session = AttendanceSession(
        date=session_data.date,
        teacher_id=session_data.teacher_id,
        subject=session_data.subject,
        class_name=session_data.class_name
    )
    session.add(new_session)
    session.commit()
    session.refresh(new_session)

    for record in session_data.records:
        new_record = AttendanceRecord(
            student_id=record.student_id,
            status=record.status,
            session_id=new_session.id,
            student_name=record.student_name
        )
        session.add(new_record)

    session.commit()
    session.refresh(new_session)
    return new_session


@router.get("/session/{session_id}/", response_model=AttendanceSessionRead)
def get_attendance_session(session_id: UUID, session: SessionDep):
    session_data = session.get(AttendanceSession, session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_data


@router.get("/student/{student_id}/", response_model=List[AttendanceRecordRead])
def get_student_attendance(student_id: UUID, session: SessionDep):
    records = session.exec(
        select(AttendanceRecord).where(AttendanceRecord.student_id == student_id)
    ).all()
    return records

from fastapi import Query
from datetime import date
from models.students import Student  # assuming Student model has `class_name`
from sqlmodel import or_

@router.get("/sessions/", response_model=List[AttendanceSessionRead])
def get_attendance_sessions(
    session: SessionDep,
    class_name: str | None = Query(None, description="Class name to filter sessions"),
    date: date | None = Query(None, description="Date to filter sessions"),
    teacher_id: UUID | None = Query(None, description="Teacher ID to filter sessions"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    offset = (page - 1) * limit
    query = select(AttendanceSession)

    # Apply filters only if provided
    # if class_name:
    #     query = query.where(AttendanceSession.class_name == class_name)
    if date:
        query = query.where(AttendanceSession.date == date)
    if teacher_id:
        query = query.where(AttendanceSession.teacher_id == teacher_id)

    # Apply pagination
    query = query.offset(offset).limit(limit)

    sessions = session.exec(query).all()
    return sessions

@router.get("/records/filter/", response_model=List[AttendanceRecordRead])
def get_filtered_attendance_records(
    session: SessionDep,
    class_name: str = Query(..., description="Class name to filter attendance"),
    date: date | None = Query(None, description="Date of the attendance session"),
    session_id: UUID | None = Query(None, description="Specific attendance session ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    offset = (page - 1) * limit

    # Get students matching class_name
    students_in_class = session.exec(
        select(Student).where(Student.class_name == class_name)
    ).all()
    student_ids = [s.id for s in students_in_class]

    if not student_ids:
        raise HTTPException(status_code=404, detail=f"No students found in class '{class_name}'")

    # Start filtering records
    query = select(AttendanceRecord).where(AttendanceRecord.student_id.in_(student_ids))

    if session_id:
        query = query.where(AttendanceRecord.session_id == session_id)

    elif date:
        sessions = session.exec(
            select(AttendanceSession.id).where(AttendanceSession.date == date)
        ).all()
        session_ids = [s[0] for s in sessions]
        if not session_ids:
            return []
        query = query.where(AttendanceRecord.session_id.in_(session_ids))

    query = query.offset(offset).limit(limit)
    records = session.exec(query).all()

    return records



@router.patch("/session/{session_id}/update", response_model=AttendanceRecordRead)
def update_or_add_attendance_record(
    session_id: UUID,
    record: AttendanceRecordUpdate,
    db: SessionDep
):
    session_obj = db.get(AttendanceSession, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Attendance session not found")

    existing_record = db.exec(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.student_id == record.student_id
        )
    ).first()

    if existing_record:
        existing_record.status = record.status
        db.add(existing_record)
        db.commit()
        db.refresh(existing_record)
        return existing_record
    else:
        new_record = AttendanceRecord(
            session_id=session_id,
            student_id=record.student_id,
            status=record.status
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record


@router.delete("/session/{session_id}/student/{student_id}/", status_code=204)
def delete_attendance_record(
    session_id: UUID,
    student_id: UUID,
    db: SessionDep
):
    record = db.exec(
        select(AttendanceRecord).where(
            AttendanceRecord.session_id == session_id,
            AttendanceRecord.student_id == student_id
        )
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    db.delete(record)
    db.commit()
    return



# cool that works
@router.get(
    "/student/{student_id}/calendar/",
    response_model=List[StudentMonthlyAttendanceEntry],
    tags=["attendance"]
)
def get_student_monthly_attendance_for_calendar(
    student_id: UUID,
    db: SessionDep,
    month: str = Query(..., description="Month in YYYY-MM format")
):
    # Parse input month string to date range
    try:
        year, month_num = map(int, month.split("-"))
        from_date = date(year, month_num, 1)
        if month_num == 12:
            to_date = date(year + 1, 1, 1)
        else:
            to_date = date(year, month_num + 1, 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.")

    # Join AttendanceRecord with AttendanceSession to filter by date
    query = (
        select(AttendanceRecord, AttendanceSession)
        .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceSession.date >= from_date,
            AttendanceSession.date < to_date
        )
    )

    results = db.exec(query).all()

    # Transform joined results into desired output structure
    attendance_list = [
        StudentMonthlyAttendanceEntry(
            date=session.date,
            status=record.status,
            subject=session.subject,
            class_name=session.class_name
        )
        for record, session in results
    ]

    return attendance_list