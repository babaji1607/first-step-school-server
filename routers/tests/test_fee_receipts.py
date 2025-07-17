import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, create_engine, Session
from main import app
from database import get_session
from Utilities.security import hash_password

# ✅ Import all models to register with metadata
from models.users import User
from models.students import Student
from models.teachers import Teacher
from models.classroom import Classroom
from models.fee_receipt import FeeReceipt

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ✅ Dependency override
def override_get_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = override_get_session

# ✅ Setup database
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    SQLModel.metadata.create_all(engine)
    yield
    # No teardown (shared DB)

@pytest.mark.asyncio
async def test_fee_receipt_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # ---------- Register a student ----------
        await client.post("/register", json={
            "email": "receipt_student@example.com",
            "password": "studentpass",
            "role": "student"
        })
        res = await client.post("/login", json={
            "email": "receipt_student@example.com",
            "password": "studentpass"
        })
        student_token = res.json()["access_token"]

        # ---------- Create student record ----------
        student_data = {
            "name": "Fee Student",
            "age": 15,
            "contact": "9999999999",
            "address": "Receipt Town",
            "FatherName": "Mr. Fee",
            "MotherName": "Mrs. Fee",
            "FatherContact": "1234567890",
            "MotherContact": "0987654321",
            "roll_number": 50,
            "date_of_birth": "2009-03-15"
        }
        create_res = await client.post("/students/create/", json=student_data,
            headers={"Authorization": f"Bearer {student_token}"})
        assert create_res.status_code == 201
        student_id = create_res.json()["id"]

        # ---------- Create fee receipt ----------
        receipt_data = {
            "student_id": student_id,
            "total_amount": 1500.50,
            "payment_reference": "TXN123456",
            "remarks": "Monthly tuition"
        }
        post_res = await client.post("/fee-receipts/", json=receipt_data,
            headers={"Authorization": f"Bearer {student_token}"})
        assert post_res.status_code == 201
        receipt = post_res.json()
        receipt_id = receipt["id"]
        assert receipt["total_amount"] == 1500.50

        # ---------- Get all receipts ----------
        all_res = await client.get("/fee-receipts/",
            headers={"Authorization": f"Bearer {student_token}"})
        assert all_res.status_code == 200
        assert any(r["id"] == receipt_id for r in all_res.json())

        # ---------- Get by receipt ID ----------
        by_id_res = await client.get(f"/fee-receipts/{receipt_id}",
            headers={"Authorization": f"Bearer {student_token}"})
        assert by_id_res.status_code == 200
        assert by_id_res.json()["id"] == receipt_id

        # ---------- Get by student ID ----------
        by_student_res = await client.get(f"/fee-receipts/student/{student_id}",
            headers={"Authorization": f"Bearer {student_token}"})
        assert by_student_res.status_code == 200
        assert any(r["id"] == receipt_id for r in by_student_res.json())
