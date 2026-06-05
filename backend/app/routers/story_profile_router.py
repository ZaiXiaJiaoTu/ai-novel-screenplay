from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.story_profile_schema import StoryProfileUpdate
from app.services.story_profile_service import (
    generate_story_profile,
    get_or_create_story_profile,
    update_story_profile,
)

router = APIRouter(prefix="/api/books", tags=["story-profiles"])


@router.get("/{book_id}/story-profile")
def get_story_profile(book_id: int, db: Session = Depends(get_db)):
    result = get_or_create_story_profile(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())


@router.post("/{book_id}/story-profile/generate")
def generate_profile(book_id: int, db: Session = Depends(get_db)):
    result = generate_story_profile(db, book_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())


@router.put("/{book_id}/story-profile")
def put_story_profile(
    book_id: int, payload: StoryProfileUpdate, db: Session = Depends(get_db)
):
    result = update_story_profile(db, book_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())
