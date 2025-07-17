import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, Session, create_engine
from uuid import UUID
from main import app
from database import get_session

from services.gallary.models import GalleryItem

# Setup in-memory SQLite
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
    SQLModel.metadata.drop_all(engine)


@pytest.mark.asyncio
async def test_gallery_crud_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        
        # ------- Register and login as teacher -------
        await client.post("/register", json={
            "email": "gallery@teacher.com",
            "password": "securepass",
            "role": "teacher"
        })
        res = await client.post("/login", json={
            "email": "gallery@teacher.com",
            "password": "securepass"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ------- Upload an image file -------
        dummy_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"  # PNG header
        files = {
            "raw_image": ("dummy.png", dummy_image, "image/png")
        }
        res = await client.post("/gallery/", files=files, headers=headers)
        assert res.status_code == 200
        gallery_id = res.json()["id"]
        assert res.json()["imageUrl"] is not None
        assert res.json()["videoUrl"] is None

        # ------- Get all gallery items -------
        res = await client.get("/gallery/")
        assert res.status_code == 200
        assert res.json()["total"] >= 1
        assert res.json()["items"][0]["id"] == gallery_id

        # ------- Get single gallery item -------
        res = await client.get(f"/gallery/{gallery_id}")
        assert res.status_code == 200
        assert res.json()["id"] == gallery_id

        # ------- Update image to video -------
        data = {
            "videoUrl": "https://youtu.be/samplevideo"
        }
        res = await client.patch(f"/gallery/{gallery_id}", data=data, headers=headers)
        assert res.status_code == 200
        assert res.json()["videoUrl"] == data["videoUrl"]
        assert res.json()["imageUrl"] is None

        # ------- Delete the gallery item -------
        res = await client.delete(f"/gallery/{gallery_id}", headers=headers)
        assert res.status_code == 200
        assert res.json()["ok"] is True


@pytest.mark.asyncio
async def test_gallery_upload_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login again
        res = await client.post("/login", json={
            "email": "gallery@teacher.com",
            "password": "securepass"
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ❌ Upload both image and video (should fail)
        dummy_image = b"fakeimage"
        files = {
            "raw_image": ("bad.png", dummy_image, "image/png")
        }
        data = {
            "videoUrl": "https://example.com/video.mp4"
        }

        res = await client.post("/gallery/", files=files, data=data, headers=headers)
        assert res.status_code == 400
        assert "Submit either an image file or a video URL" in res.json()["detail"]

        # ❌ Upload neither image nor video (should fail)
        res = await client.post("/gallery/", headers=headers)
        assert res.status_code == 400
        assert "Submit either an image file or a video URL" in res.json()["detail"]
