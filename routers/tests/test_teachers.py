import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session

from models.users import User
from models.teachers import Teacher
from models.students import Student
from models.classroom import Classroom
from Utilities.security import hash_password

# Test DB
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Dependency override
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# Setup DB before module, teardown after
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    # SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_teachers_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # ---------- Register teacher user ----------
        email = "teacher@example.com"
        password = "teachpass123"

        await client.post("/register", json={
            "email": email,
            "password": password,
            "role": "teacher"
        })

        res = await client.post("/login", json={
            "email": email,
            "password": password
        })
        assert res.status_code == 200
        token = res.json()["access_token"]

        # ---------- Create Teacher ----------
        teacher_data = {
            "name": "Jane Smith",
            "age": 30,
            "contact": "1234567890",
            "subject": "Mathematics",
            "address": "123 Education Lane",
        }  # something fishy here as teacher with token is able to create teacher with his own token damn
        create_res = await client.post("/teachers/create/", json=teacher_data,
            headers={"Authorization": f"Bearer {token}"})
        assert create_res.status_code == 201
        teacher_id = create_res.json()["id"]

        # ---------- Get All Teachers ----------
        all_teachers = await client.get("/teachers/showall/",
            headers={"Authorization": f"Bearer {token}"})
        assert all_teachers.status_code == 200
        assert any(t["id"] == teacher_id for t in all_teachers.json())

        # ---------- Get Teacher by ID ----------
        get_teacher = await client.get(f"/teachers/teacher/{teacher_id}/",
            headers={"Authorization": f"Bearer {token}"})
        assert get_teacher.status_code == 200
        assert get_teacher.json()["name"] == teacher_data["name"]

        # ---------- Update Teacher ----------
        updated_data = {
            "name": "Jane Updated",
            "age": 31,
            "contact": "9876543210",
            "subject": "Physics",
            "address": "456 Science St",
            "user_id": None  # Avoids conflict if not set
        }
        update = await client.put(f"/teachers/teacher/{teacher_id}/", json=updated_data,
            headers={"Authorization": f"Bearer {token}"})
        assert update.status_code == 200
        assert update.json()["name"] == "Jane Updated"

        # ---------- Delete Teacher ----------
        delete = await client.delete(f"/teachers/teacher/{teacher_id}",
            headers={"Authorization": f"Bearer {token}"})
        assert delete.status_code == 200
        assert delete.json()["ok"] is True
