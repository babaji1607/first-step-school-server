# routers/students.py
from fastapi import APIRouter, HTTPException, status
from database import db
from models import Student, StudentInDB, AttendanceUpdate, AttendanceResponse

router = APIRouter(
    prefix="/students",
    tags=["students"]
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=Student)
async def create_student(student: Student):
    success = db.add_student(student.student_id, student.name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with ID {student.student_id} already exists"
        )
    return student

@router.get("/", response_model=list[StudentInDB])
async def get_all_students():
    return db.get_all_students()

@router.get("/{student_id}", response_model=StudentInDB)
async def get_student(student_id: str):
    student = db.get_student(student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    return student

@router.post("/attendance/mark-absences", response_model=AttendanceResponse)
async def mark_absences(attendance: AttendanceUpdate):
    if len(db.students) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No students registered in the system"
        )
    return db.mark_absences(attendance.date, attendance.absent_students)

@router.get("/attendance/{date}", response_model=AttendanceResponse)
async def get_attendance(date: str):
    return db.get_attendance(date)

@router.get("/attendance/report/monthly/{year}/{month}", response_model=dict)
async def monthly_attendance_report(year: int, month: int):
    return db.get_monthly_report(year, month)