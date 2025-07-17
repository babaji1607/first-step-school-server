import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from uuid import uuid4
from datetime import datetime
from main import app
from database import get_session

from services.diary.models import DiaryItem

# Use in-memory SQLite or test.db
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Override FastAPI dependency
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_diary_crud_flow_with_file_upload():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ----------- Register & login as teacher -----------
        await client.post("/register", json={
            "email": "teacher@diary.com",
            "password": "password123",
            "role": "teacher"
        })
        res = await client.post("/login", json={
            "email": "teacher@diary.com",
            "password": "password123"
        })
        token = res.json()["access_token"]
        auth_header = {"Authorization": f"Bearer {token}"}

        # ----------- Upload diary item with file -----------
        dummy_pdf = b"%PDF-1.4 Dummy PDF Content"
        files = {
            "raw_file": ("test.pdf", dummy_pdf, "application/pdf")
        }
        data = {
            "title": "Homework",
            "classname": "10B",
            "teacher_name": "Mr. Sharma",
            "description": "Today's homework details"
        }

        res = await client.post(
            "/diary/",
            data=data,
            files=files,
            headers=auth_header
        )
        assert res.status_code == 200
        diary_id = res.json()["id"]
        assert res.json()["file_url"] is not None

        # ----------- Get all diary items -----------
        res = await client.get("/diary/", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["total"] >= 1

        # ----------- Filter by class name -----------
        res = await client.get("/diary/by-class", params={"classname": "10B"}, headers=auth_header)
        assert res.status_code == 200
        assert res.json()["items"][0]["title"] == "Homework"

        # ----------- Filter by teacher name -----------
        res = await client.get("/diary/by-teacher", params={"teacher_name": "Mr. Sharma"}, headers=auth_header)
        assert res.status_code == 200
        assert res.json()["items"][0]["classname"] == "10B"

        # ----------- Update diary (PUT) -----------
        updated_data = {
            "title": "Updated Homework",
            "classname": "10B",
            "teacher_name": "Mr. Sharma",
            "description": "Updated description",
            "file_url": res.json()["items"][0]["file_url"]  # keep file_url
        }
        res = await client.put(f"/diary/{diary_id}", json=updated_data, headers=auth_header)
        assert res.status_code == 200
        assert res.json()["title"] == "Updated Homework"

        # ----------- Delete diary item -----------
        res = await client.delete(f"/diary/{diary_id}", headers=auth_header)
        assert res.status_code == 200
        assert res.json()["ok"] is True
