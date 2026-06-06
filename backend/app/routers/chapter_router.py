from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.chapter_schema import ChapterCreate, ChapterUpdate
from app.services.chapter_service import (
    create_chapter,
    delete_chapter,
    get_chapter_detail,
    update_chapter,
)

router = APIRouter(tags=["chapters"])


@router.get("/api/chapters/{chapter_id}")
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    result = get_chapter_detail(db, chapter_id)
    if result is None:
        raise HTTPException(status_code=404, detail="chapter not found")
    return success(result.model_dump())


@router.post("/api/books/{book_id}/chapters")
def create_book_chapter(
    book_id: int, payload: ChapterCreate, db: Session = Depends(get_db)
):
    result = create_chapter(db, book_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="book not found")
    return success(result.model_dump())


@router.put("/api/chapters/{chapter_id}")
def update_book_chapter(
    chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)
):
    result = update_chapter(db, chapter_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="chapter not found")
    return success(result.model_dump())


@router.delete("/api/chapters/{chapter_id}")
def delete_book_chapter(chapter_id: int, db: Session = Depends(get_db)):
    result = delete_chapter(db, chapter_id)
    if result is None:
        raise HTTPException(status_code=404, detail="chapter not found")
    return success(result.model_dump())
