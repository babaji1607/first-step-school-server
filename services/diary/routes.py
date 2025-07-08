from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, Body
from typing import Optional, Union
from uuid import UUID
from sqlmodel import select
from database import SessionDep
from Utilities.auth import require_min_role
from Utilities.s3bucketupload import upload_to_s3, delete_from_s3
from services.diary.models import DiaryItem, DiaryCreate, DiaryUpdate, DiaryRead, DiaryPaginationResponse

Diary_router = APIRouter(
    prefix="/diary",
    tags=["Diary"],
    dependencies=[Depends(require_min_role("student"))],  # ✅ Read access for students
)

def normalize_upload_file(file: Union[UploadFile, str, None]) -> Optional[UploadFile]:
    if isinstance(file, str) and file.strip() == "":
        return None
    return file

@Diary_router.post("/", response_model=DiaryRead, dependencies=[Depends(require_min_role("teacher"))])
async def create_diary_item(
    session: SessionDep,
    title: str = Form(...),
    classname: str = Form(...),
    teacher_name: str = Form(...),  # ✅ New field
    description: Optional[str] = Form(None),
    raw_file: Union[UploadFile, str, None] = File(None),
):
    file = normalize_upload_file(raw_file)
    file_url = None

    if file:
        try:
            file_url = upload_to_s3(file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    diary_data = DiaryCreate(
        title=title,
        classname=classname,
        teacher_name=teacher_name,
        description=description,
        file_url=file_url,
    )

    new_entry = DiaryItem.from_orm(diary_data)
    session.add(new_entry)
    session.commit()
    session.refresh(new_entry)
    return new_entry

@Diary_router.get("/", response_model=DiaryPaginationResponse)
def get_all_diary_items(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    total_items = session.exec(select(DiaryItem)).all()
    paginated_items = session.exec(
        select(DiaryItem)
        .order_by(DiaryItem.creation_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "total": len(total_items),
        "offset": offset,
        "limit": limit,
        "items": paginated_items
    }

@Diary_router.get("/by-class", response_model=DiaryPaginationResponse)
def get_diary_by_classname(
    session: SessionDep,
    classname: str = Query(..., min_length=1),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
):
    total_items = session.exec(
        select(DiaryItem).where(DiaryItem.classname == classname)
    ).all()

    paginated_items = session.exec(
        select(DiaryItem)
        .where(DiaryItem.classname == classname)
        .order_by(DiaryItem.creation_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return DiaryPaginationResponse(
        total=len(total_items),
        offset=offset,
        limit=limit,
        items=paginated_items
    )

@Diary_router.get("/by-teacher", response_model=DiaryPaginationResponse)
def get_diary_by_teacher(
    session: SessionDep,
    teacher_name: str = Query(..., min_length=1),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=100),
):
    total_items = session.exec(
        select(DiaryItem).where(DiaryItem.teacher_name == teacher_name)
    ).all()

    paginated_items = session.exec(
        select(DiaryItem)
        .where(DiaryItem.teacher_name == teacher_name)
        .order_by(DiaryItem.creation_date.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return DiaryPaginationResponse(
        total=len(total_items),
        offset=offset,
        limit=limit,
        items=paginated_items,
    )

@Diary_router.get("/{item_id}", response_model=DiaryRead)
def get_diary_item(item_id: UUID, session: SessionDep):
    item = session.get(DiaryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Diary entry not found")
    return item

@Diary_router.put("/{item_id}", response_model=DiaryRead, dependencies=[Depends(require_min_role("teacher"))])
def replace_diary_item_json(
    session: SessionDep,
    item_id: UUID,
    updated_data: DiaryCreate = Body(...),
):
    db_item = session.get(DiaryItem, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Diary entry not found")

    db_item.title = updated_data.title
    db_item.description = updated_data.description
    db_item.classname = updated_data.classname
    db_item.teacher_name = updated_data.teacher_name  # ✅ Update teacher name
    db_item.file_url = updated_data.file_url

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@Diary_router.delete("/{item_id}", dependencies=[Depends(require_min_role("teacher"))])
def delete_diary_item(item_id: UUID, session: SessionDep):
    item = session.get(DiaryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Diary entry not found")

    if item.file_url:
        try:
            filename = item.file_url.split("/")[-1].split("?")[0]
            delete_from_s3(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")

    session.delete(item)
    session.commit()
    return {"ok": True}
