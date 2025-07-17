import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from main import app
from database import get_session
from Utilities.security import hash_password
from models.users import User
from models.events import Event
from uuid import UUID
from datetime import datetime
from unittest.mock import patch
import io

# Setup SQLite test DB
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    # SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_events_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------- Register and login student ----------
        await client.post("/register", json={
            "email": "student1@example.com",
            "password": "studentpass",
            "role": "student"
        })
        res = await client.post("/login", json={
            "email": "student1@example.com",
            "password": "studentpass"
        })
        student_token = res.json()["access_token"]

        # ---------- Upload dummy event with mocked S3 ----------
        dummy_file = io.BytesIO(b"fake image data")
        dummy_file.name = "test.jpg"

        with patch("routers.events.upload_to_s3") as mock_upload:
            mock_upload.return_value = "https://s3.bucket/test.jpg"

            res = await client.post(
                "/events/",
                headers={"Authorization": f"Bearer {student_token}"},
                files={
                    "image": ("test.jpg", dummy_file, "image/jpeg")
                },
                data={
                    "title": "Sports Day",
                    "description": "Annual sports day at school",
                    "event_date": datetime.utcnow().isoformat()
                }
            )
        
        assert res.status_code == 200
        event = res.json()
        event_id = event["id"]
        assert event["title"] == "Sports Day"
        assert event["imageUrl"] == "https://s3.bucket/test.jpg"

        # ---------- Get by ID ----------
        res = await client.get(f"/events/{event_id}",
                               headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 200
        assert res.json()["title"] == "Sports Day"

        # ---------- Update Status ----------
        res = await client.patch(f"/events/{event_id}/status?status=inactive",
                                 headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 200
        assert res.json()["status"] == "inactive"

        # ---------- Get Active Events ----------
        res = await client.get("/events/active",
                               headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 200
        assert all(ev["status"] == "active" for ev in res.json()) or len(res.json()) == 0

        # ---------- Delete Event (Mock delete_from_s3) ----------
        with patch("routers.events.delete_from_s3") as mock_delete:
            mock_delete.return_value = None
            res = await client.delete(f"/events/{event_id}",
                                      headers={"Authorization": f"Bearer {student_token}"})
            assert res.status_code == 200
            assert res.json()["ok"] is True
