import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session
from Utilities.security import hash_password

# ✅ Import models to register them with SQLModel metadata
from models.users import User
from models.students import Student
from models.teachers import Teacher
from models.classroom import Classroom

# Create test engine
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Override FastAPI DB session with test session
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# ✅ Setup DB and teardown after tests
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    # SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_students_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------- Register student ----------
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

        # ---------- Create admin directly ----------
        with Session(engine) as session:
            admin = User(
                email="admin@student.com",
                hashed_password=hash_password("adminpass"),
                role="admin"
            )
            session.add(admin)
            session.commit()

        res = await client.post("/login", json={
            "email": "admin@student.com",
            "password": "adminpass"
        })
        admin_token = res.json()["access_token"]

        # ---------- Create student ----------
        student_data = {
            "name": "John Doe",
            "age": 16,
            "contact": "1234567890",
            "address": "123 Main St",
            "FatherName": "John Sr.",
            "MotherName": "Jane",
            "FatherContact": "9876543210",
            "MotherContact": "8765432109",
            "roll_number": 21,
            "date_of_birth": "2008-05-10"
        }
        create_res = await client.post("/students/create/", json=student_data,
            headers={"Authorization": f"Bearer {student_token}"})
        assert create_res.status_code == 201
        student_id = create_res.json()["id"]

        # ---------- Show all (admin) ----------
        showall = await client.get("/students/showall/",
            headers={"Authorization": f"Bearer {admin_token}"})
        assert showall.status_code == 200
        assert any(s["id"] == student_id for s in showall.json())

        # ---------- Search by term ----------
        search_term = await client.get("/students/search/by-term/?query=John",
            headers={"Authorization": f"Bearer {student_token}"})
        assert search_term.status_code == 200

        # ---------- Search by field ----------
        search_filter = await client.get("/students/search/?name=John",
            headers={"Authorization": f"Bearer {student_token}"})
        assert search_filter.status_code == 200
        assert search_filter.json()["results"][0]["id"] == student_id

        # ---------- Update ----------
        updated = {
            "name": "Johnny Doe",
            "age": 17,
            "contact": "1112223333",
            "address": "New Street",
            "FatherName": "Johnny Sr.",
            "MotherName": "Janet",
            "FatherContact": "7778889990",
            "MotherContact": "6665554440",
            "roll_number": 99,
            "date_of_birth": "2007-01-01"
        }
        update = await client.put(f"/students/student/{student_id}/", json=updated,
            headers={"Authorization": f"Bearer {student_token}"})
        assert update.status_code == 200
        assert update.json()["name"] == "Johnny Doe"

        # ---------- Delete ----------
        delete = await client.delete(f"/students/student/{student_id}",
            headers={"Authorization": f"Bearer {student_token}"})
        assert delete.status_code == 200
        assert delete.json()["ok"] is True
