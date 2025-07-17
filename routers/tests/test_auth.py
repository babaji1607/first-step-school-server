import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session

# ✅ Import all models BEFORE create_all to register tables!
from models.users import User
from models.students import Student
from models.teachers import Teacher
from models.classroom import Classroom

from Utilities.security import hash_password

# --- Test DB Setup ---
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# --- Override DB Session for Dependency Injection ---
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# --- DB Fixture (creates & drops tables) ---
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)  # Make sure all tables are created
    yield
    # SQLModel.metadata.drop_all(engine)✅ Keep drop_all() only in one place (ideally once before all tests start).

# ❌ Do not drop tables after every module, or you'll affect other modules running later

# --- Combined Auth Test ---
@pytest.mark.asyncio
async def test_auth_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # ---------- Register Student ----------
        student_email = "student@example.com"
        student_password = "password123"
        res = await client.post("/register", json={
            "email": student_email,
            "password": student_password,
            "role": "student"
        })
        assert res.status_code == 200

        res = await client.post("/login", json={
            "email": student_email,
            "password": student_password
        })
        assert res.status_code == 200
        student_token = res.json()["access_token"]

        # ---------- Create Admin User ----------
        with Session(engine) as session:
            admin = User(
                email="admin@example.com",
                hashed_password=hash_password("adminpass"),
                role="admin"
            )
            session.add(admin)
            session.commit()
            session.refresh(admin)
            admin_user_id = str(admin.id)

        res = await client.post("/login", json={
            "email": "admin@example.com",
            "password": "adminpass"
        })
        assert res.status_code == 200
        admin_token = res.json()["access_token"]

        # ---------- /me ----------
        me = await client.get("/me", headers={"Authorization": f"Bearer {student_token}"})
        assert me.status_code == 200
        assert me.json()["email"] == student_email

        # ---------- /admin-area (forbidden for student) ----------
        admin_fail = await client.get("/admin-area", headers={"Authorization": f"Bearer {student_token}"})
        assert admin_fail.status_code == 403

        # ---------- /admin-area (allowed for admin) ----------
        admin_area = await client.get("/admin-area", headers={"Authorization": f"Bearer {admin_token}"})
        assert admin_area.status_code == 200

        # ---------- /users ----------
        users_list = await client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert users_list.status_code == 200

        # ---------- /admin/reset-password ----------
        reset = await client.post("/admin/reset-password", json={
            "user_email": student_email,
            "new_password": "newpass123"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert reset.status_code == 200

        # ---------- Login with new password ----------
        relogin = await client.post("/login", json={
            "email": student_email,
            "password": "newpass123"
        })
        assert relogin.status_code == 200

        # ---------- /users/{id} DELETE ----------
        delete = await client.delete(f"/users/{admin_user_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert delete.status_code == 200
