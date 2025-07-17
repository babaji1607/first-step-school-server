import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from uuid import UUID
from main import app
from database import get_session
from Utilities.security import hash_password
from models.users import User
from models.classroom import Classroom
from models.teachers import Teacher

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
async def test_classrooms_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------- Register & login teacher ----------
        await client.post("/register", json={
            "email": "teacher1@example.com",
            "password": "teacherpass",
            "role": "teacher"
        })
        res = await client.post("/login", json={
            "email": "teacher1@example.com",
            "password": "teacherpass"
        })
        teacher_token = res.json()["access_token"]

        # ---------- Create admin manually for /showall ----------
        with Session(engine) as session:
            admin = User(email="admin@classroom.com", hashed_password=hash_password("adminpass"), role="admin")
            session.add(admin)
            session.commit()

        res = await client.post("/login", json={
            "email": "admin@classroom.com",
            "password": "adminpass"
        })
        admin_token = res.json()["access_token"]

        # ---------- Create teacher manually ----------
        with Session(engine) as session:
            teacher = Teacher(
                name="Mrs. Smith",
                age=35,
                contact="9991112222",
                subject="Science",
                address="School Street",
                user_id=None
            )
            session.add(teacher)
            session.commit()
            teacher_id = teacher.id

        # ---------- Create classroom ----------
        classroom_data = {
            "name": "10A",
            "teacher_id": str(teacher_id)
        }
        res = await client.post("/classrooms/create", json=classroom_data,
                                headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 201
        classroom_id = res.json()["id"]

        # ---------- Get all names ----------
        res = await client.get("/classrooms/names", headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert "10A" in res.json()

        # ---------- Show all classrooms (admin) ----------
        res = await client.get("/classrooms/showall", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert any(c["id"] == classroom_id for c in res.json())

        # ---------- Search classrooms ----------
        res = await client.get("/classrooms/search?name=10A", headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()["results"][0]["name"] == "10A"

        # ---------- Get by ID ----------
        res = await client.get(f"/classrooms/classroom/{classroom_id}",
                               headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()["id"] == classroom_id

        # ---------- Update ----------
        updated_data = {
            "name": "10B",
            "teacher_id": str(teacher_id)
        }
        res = await client.put(f"/classrooms/classroom/{classroom_id}", json=updated_data,
                               headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()["name"] == "10B"

        # ---------- Get classrooms by teacher ----------
        res = await client.get(f"/classrooms/by-teacher/{teacher_id}",
                               headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert any(c["id"] == classroom_id for c in res.json())

        # ---------- Delete classroom ----------
        res = await client.delete(f"/classrooms/classroom/{classroom_id}",
                                  headers={"Authorization": f"Bearer {teacher_token}"})
        assert res.status_code == 200
        assert res.json()["ok"] is True
