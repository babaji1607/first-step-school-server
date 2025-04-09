# models.py
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class Student(BaseModel):
    student_id: str
    name: str

class StudentInDB(Student):
    id: int

class AttendanceUpdate(BaseModel):
    date: str = datetime.now().strftime("%Y-%m-%d")
    absent_students: List[str]

class AttendanceResponse(BaseModel):
    date: str
    total_students: int
    present_count: int
    absent_count: int
    absent_students: List[Dict[str, str]]

class MonthlyReportResponse(BaseModel):
    year: int
    month: int
    total_students: int
    dates_with_absences: List[str]
    student_absence_summary: List[Dict[str, str | int]]
    daily_absence_counts: Dict[str, int]

class APIInfo(BaseModel):
    name: str
    version: str
    description: str
    endpoints: List[str]