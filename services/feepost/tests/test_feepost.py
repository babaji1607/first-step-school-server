import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, Session, create_engine
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from main import app
from database import get_session

from models.students import Student
from services.feepost.models import FeeMode

# Set up test DB
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
async def test_fee_post_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # ---------- Create a student manually ----------
        with Session(engine) as session:
            student = Student(
                name="FeePost Student",
                age=14,
                contact="1112223334",
                address="Test Lane",
                FatherName="Dad",
                MotherName="Mom",
                FatherContact="1234567890",
                MotherContact="0987654321",
                roll_number=1001,
                date_of_birth=datetime(2010, 1, 1),
                class_name="8A"
            )
            session.add(student)
            session.commit()
            student_id = student.id

        # ---------- Register & login admin ----------
        await client.post("/register", json={
            "email": "admin@feetest.com",
            "password": "adminpass",
            "role": "admin"
        })
        res = await client.post("/login", json={
            "email": "admin@feetest.com",
            "password": "adminpass"
        })
        admin_token = res.json()["access_token"]

        # ---------- Register & login student ----------
        await client.post("/register", json={
            "email": "student@feetest.com",
            "password": "studentpass",
            "role": "student"
        })
        res = await client.post("/login", json={
            "email": "student@feetest.com",
            "password": "studentpass"
        })
        student_token = res.json()["access_token"]

        # ---------- Create FeePost ----------
        fee_payload = {
            "student_id": str(student_id),
            "title": "Monthly Tuition",
            "other_fee": {"Lab Fee": 200.0, "Library Fee": 100.0},
            "deadline": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "is_paid": False,
            "mode": "offline"
        }
        res = await client.post("/feepost/", json=fee_payload,
                                headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        fee_post_id = res.json()["id"]

        # ---------- Get all fee posts ----------
        # ---------- Get all fee posts (requires student auth) ----------
        res = await client.get(
            "/feepost/",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert res.status_code == 200
        assert res.json()["total"] >= 1

        # ---------- Filter fee posts by student (requires student auth) ----------
        res = await client.get(
            f"/feepost/by-student?student_id={student_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert res.status_code == 200
        assert res.json()["total"] == 1
        assert res.json()["items"][0]["title"] == "Monthly Tuition"

        # ---------- Update fee post status ----------
        update_payload = {
            "mode": "online",
            "is_paid": True
        }
        res = await client.patch(f"/feepost/{fee_post_id}/status", json=update_payload,
                                 headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 200
        assert res.json()["is_paid"] is True
        assert res.json()["mode"] == "online"

        # ---------- Delete fee post ----------
        res = await client.delete(f"/feepost/{fee_post_id}",
                                  headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.json()["ok"] is True
