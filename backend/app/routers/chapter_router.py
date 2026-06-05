from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.services.chapter_summary_service import (
    generate_chapter_summaries,
    get_chapter_detail,
    get_chapter_summary,
)

router = APIRouter(tags=["chapters"])


@router.get("/api/chapters/{chapter_id}")
def get_chapter(chapter_id: int, db: Session = Depends(get_db)):
    result = get_chapter_detail(db, chapter_id)
    if result is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    return success(result.model_dump())


@router.get("/api/chapters/{chapter_id}/summary")
def get_summary(chapter_id: int, db: Session = Depends(get_db)):
    result = get_chapter_summary(db, chapter_id)
    if result is None:
        raise HTTPException(status_code=404, detail="章节摘要不存在")
    return success(result.model_dump())


@router.post("/api/books/{book_id}/chapter-summaries/generate")
def generate_summaries(book_id: int, db: Session = Depends(get_db)):
    result = generate_chapter_summaries(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())
