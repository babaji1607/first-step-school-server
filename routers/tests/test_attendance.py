import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session
from Utilities.security import hash_password
from uuid import UUID
from datetime import date

# ✅ Import models
from models.users import User
from models.students import Student
from models.teachers import Teacher
from models.attendance import AttendanceSession, AttendanceRecord

# Setup test DB
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    # SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_attendance_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ---------- Register & login teacher ----------
        await client.post("/register", json={
            "email": "teacher1@attend.com",
            "password": "teacherpass",
            "role": "teacher"
        })
        res = await client.post("/login", json={
            "email": "teacher1@attend.com",
            "password": "teacherpass"
        })
        teacher_token = res.json()["access_token"]

        # ---------- Create teacher & student manually ----------
        with Session(engine) as session:
            teacher = Teacher(name="Mr. Att", age=35, contact="1231231234", subject="Math", address="Block 1")
            student = Student(name="Student One", age=15, contact="4564564567", address="Block 2",
                              FatherName="Dad", MotherName="Mom", FatherContact="9990001112", MotherContact="8887776665",
                              roll_number=101, date_of_birth=date(2008, 9, 1), class_name="10A")
            session.add(teacher)
            session.add(student)
            session.commit()
            teacher_id = teacher.id
            student_id = student.id

        # ---------- Create session with attendance record ----------
        attendance_payload = {
            "date": "2025-07-16",
            "teacher_id": str(teacher_id),
            "subject": "Math",
            "class_name": "10A",
            "records": [
                {
                    "student_id": str(student_id),
                    "status": "present",
                    "student_name": "Student One"
                }
            ]
        }
        res = await client.post("/attendance/", json=attendance_payload,
                                headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 201
        session_id = res.json()["id"]
        record_id = res.json()["records"][0]["id"]

        # ---------- Fetch session by ID ----------
        res = await client.get(f"/attendance/session/{session_id}/",
                               headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()["records"][0]["student_id"] == str(student_id)

        # ---------- Fetch attendance by student ----------
        res = await client.get(f"/attendance/student/{student_id}/",
                               headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert len(res.json()) == 1

        # ---------- Update record status ----------
        update_payload = {
            "student_id": str(student_id),
            "status": "absent"
        }
        res = await client.patch(f"/attendance/session/{session_id}/update", json=update_payload,
                                 headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()["status"] == "absent"

        # ---------- Fetch calendar view ----------
        res = await client.get(f"/attendance/student/{student_id}/calendar/?month=2025-07",
                               headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()[0]["status"] == "absent"

        # ---------- Delete attendance record ----------
        res = await client.delete(f"/attendance/session/{session_id}/student/{student_id}/",
                                  headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 204

        # ---------- Delete session ----------
        res = await client.delete(f"/attendance/session/{session_id}/",
                                  headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 204
