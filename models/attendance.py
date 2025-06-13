from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import UUID, uuid4
from datetime import date


class AttendanceRecordBase(SQLModel):
    student_id: UUID
    status: str  # "present", "absent", etc.
    student_name: str|None = None


class AttendanceRecord(AttendanceRecordBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="attendancesession.id")
    session: Optional["AttendanceSession"] = Relationship(back_populates="records")


class AttendanceRecordRead(AttendanceRecordBase):
    id: UUID
    session_id: UUID


class AttendanceRecordCreate(AttendanceRecordBase):
    pass


class AttendanceSessionBase(SQLModel):
    date: date
    teacher_id: UUID
    subject: str
    class_name: str


class AttendanceSession(AttendanceSessionBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    records: list[AttendanceRecord] = Relationship(back_populates="session")


class AttendanceSessionCreate(AttendanceSessionBase):
    records: list[AttendanceRecordCreate]


class AttendanceSessionRead(AttendanceSessionBase):
    id: UUID
    records: list[AttendanceRecordRead] = []

class AttendanceRecordUpdate(SQLModel):
    student_id: UUID
    status: str  # "present", "absent", etc.
    student_name: str | None = None
    
    
class StudentMonthlyAttendanceEntry(SQLModel):
    date: date
    status: str
    subject: str
    class_name: str