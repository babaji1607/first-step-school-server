# routers/admin.py
from fastapi import APIRouter, HTTPException, status
from database import db

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)

# Example admin endpoints
@router.get("/system-stats")
async def get_system_stats():
    return {
        "students_count": len(db.students),
        "attendance_records": sum(len(v) for v in db.attendance.values())
    }

# Add more admin-specific endpoints