from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.book_schema import BookTextCreate
from app.services.book_service import (
    create_book_from_text,
    delete_book,
    get_book_detail,
    list_book_chapters,
    list_books,
)

router = APIRouter(prefix="/api/books", tags=["books"])


@router.post("/text")
def create_book_by_text(payload: BookTextCreate, db: Session = Depends(get_db)):
    try:
        result = create_book_from_text(db, title=payload.title, content=payload.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success(result.model_dump())


@router.post("/upload")
async def upload_book(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("gb18030")

    book_title = title or file.filename.rsplit(".", 1)[0]
    try:
        result = create_book_from_text(
            db,
            title=book_title,
            content=content,
            source_type="file",
            original_filename=file.filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success(result.model_dump())


@router.get("")
def get_books(
    keyword: str | None = None,
    novel_type: str | None = Query(default=None, pattern="^(short|middle|long)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return success(
        list_books(
            db, keyword=keyword, novel_type=novel_type, page=page, size=size
        ).model_dump()
    )


@router.get("/{book_id}")
def get_book(book_id: int, db: Session = Depends(get_db)):
    result = get_book_detail(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())


@router.delete("/{book_id}")
def remove_book(book_id: int, db: Session = Depends(get_db)):
    result = delete_book(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())


@router.get("/{book_id}/chapters")
def get_chapters(book_id: int, db: Session = Depends(get_db)):
    result = list_book_chapters(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success([item.model_dump() for item in result])
