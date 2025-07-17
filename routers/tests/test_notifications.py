import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from uuid import UUID
from main import app
from database import get_session
from Utilities.security import hash_password

# ✅ Register models with metadata
from models.users import User
from models.students import Student
from models.teachers import Teacher
from models.classroom import Classroom
from models.notifications import Notification

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ✅ Override DB session
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    # No drop to avoid breaking other tests

@pytest.mark.asyncio
async def test_notifications_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------- Register a student ----------
        await client.post("/register", json={
            "email": "notify_student@example.com",
            "password": "studentpass",
            "role": "student"
        })
        res = await client.post("/login", json={
            "email": "notify_student@example.com",
            "password": "studentpass"
        })
        student_token = res.json()["access_token"]

        # ---------- Create a notification ----------
        notification_data = {
            "title": "Test Alert",
            "message": "This is a test notification",
            "recipient_type": "student"
        }
        create_res = await client.post("/notifications/", json=notification_data,
            headers={"Authorization": f"Bearer {student_token}"})
        assert create_res.status_code == 200
        notif = create_res.json()
        notification_id = notif["id"]
        assert notif["title"] == "Test Alert"

        # ---------- Get notification by type ----------
        by_type = await client.get("/notifications/by-type/student",
            headers={"Authorization": f"Bearer {student_token}"})
        assert by_type.status_code == 200
        assert any(n["id"] == notification_id for n in by_type.json())

        # ---------- Mark as read ----------
        mark_read = await client.patch(f"/notifications/{notification_id}/read",
            headers={"Authorization": f"Bearer {student_token}"})
        assert mark_read.status_code == 200
        assert mark_read.json()["is_read"] is True

        # ---------- Delete notification ----------
        delete = await client.delete(f"/notifications/{notification_id}",
            headers={"Authorization": f"Bearer {student_token}"})
        assert delete.status_code == 200
        assert delete.json()["ok"] is True
