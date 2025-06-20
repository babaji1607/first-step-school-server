from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlmodel import select
from typing import Optional, Union
from uuid import UUID
from services.gallary.models import (
    GalleryItem,
    GalleryItemCreate,
    GalleryItemUpdate,
    GalleryItemRead,
)
from Utilities.auth import require_min_role
from Utilities.s3bucketupload import upload_to_s3, delete_from_s3
from database import SessionDep

Gallary_route = APIRouter(
    prefix="/gallery",
    tags=["Gallery"],
    dependencies=[Depends(require_min_role("admin"))],  # Only admin access
)

# Helper to convert blank image input to None
def normalize_upload_file(image: Union[UploadFile, str, None]) -> Optional[UploadFile]:
    if isinstance(image, str) and image.strip() == "":
        return None
    return image

@Gallary_route.post("/", response_model=GalleryItemRead)
async def create_gallery_item(
    session: SessionDep,
    raw_image: Union[UploadFile, str, None] = File(None),
    videoUrl: Optional[str] = Form(None),
):
    image = normalize_upload_file(raw_image)

    if (image and videoUrl) or (not image and not videoUrl):
        raise HTTPException(
            status_code=400,
            detail="Submit either an image file or a video URL, but not both.",
        )

    imageUrl = None
    if image:
        try:
            imageUrl = upload_to_s3(image)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

    item_data = GalleryItemCreate(
        imageUrl=imageUrl,
        videoUrl=videoUrl if not image else None,
    )

    new_item = GalleryItem.from_orm(item_data)
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return new_item


@Gallary_route.get("/", response_model=list[GalleryItemRead])
def get_all_gallery_items(session: SessionDep):
    return session.exec(select(GalleryItem)).all()


@Gallary_route.get("/{item_id}", response_model=GalleryItemRead)
def get_gallery_item(item_id: UUID, session: SessionDep):
    item = session.get(GalleryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    return item


@Gallary_route.patch("/{item_id}", response_model=GalleryItemRead)
async def update_gallery_item(
    item_id: UUID,
    session: SessionDep,
    raw_image: Union[UploadFile, str, None] = File(None),
    videoUrl: Optional[str] = Form(None),
):
    image = normalize_upload_file(raw_image)

    if (image and videoUrl) or (not image and not videoUrl):
        raise HTTPException(
            status_code=400,
            detail="Submit either an image file or a video URL, but not both.",
        )

    db_item = session.get(GalleryItem, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Gallery item not found")

    if image:
        if db_item.imageUrl:
            try:
                filename = db_item.imageUrl.split("/")[-1].split("?")[0]
                delete_from_s3(filename)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete old image: {str(e)}")

        try:
            db_item.imageUrl = upload_to_s3(image)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        db_item.videoUrl = None

    if videoUrl:
        if db_item.imageUrl:
            try:
                filename = db_item.imageUrl.split("/")[-1].split("?")[0]
                delete_from_s3(filename)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to delete image: {str(e)}")

        db_item.imageUrl = None
        db_item.videoUrl = videoUrl

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@Gallary_route.delete("/{item_id}")
def delete_gallery_item(item_id: UUID, session: SessionDep):
    item = session.get(GalleryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")

    if item.imageUrl:
        try:
            filename = item.imageUrl.split("/")[-1].split("?")[0]
            delete_from_s3(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete image from S3: {str(e)}")

    session.delete(item)
    session.commit()
    return {"ok": True}
