from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.story_profile import StoryProfile
from app.schemas.story_profile_schema import StoryProfileDetail, StoryProfileUpdate


def build_initial_story_profile(book: Book, chapters: list[Chapter]) -> StoryProfile:
    chapter_outlines = [
        {
            "chapter_index": chapter.chapter_index,
            "title": chapter.title,
            "summary": "",
        }
        for chapter in chapters
    ]
    return StoryProfile(
        book_id=book.id,
        title=book.title,
        genre=book.novel_type,
        overview=f"《{book.title}》的故事设定档案待完善。",
        world_setting="",
        main_conflict="",
        characters=[],
        relationships=[],
        key_events=[],
        chapter_outlines=chapter_outlines,
        clues=[],
        tone="",
        locked_settings=[],
        version=1,
        confirmed=False,
    )


def serialize_story_profile(profile: StoryProfile) -> StoryProfileDetail:
    return StoryProfileDetail(
        profile_id=profile.id,
        book_id=profile.book_id,
        title=profile.title,
        genre=profile.genre,
        overview=profile.overview,
        world_setting=profile.world_setting,
        main_conflict=profile.main_conflict,
        characters=profile.characters,
        relationships=profile.relationships,
        key_events=profile.key_events,
        chapter_outlines=profile.chapter_outlines,
        clues=profile.clues,
        tone=profile.tone,
        locked_settings=profile.locked_settings,
        version=profile.version,
        confirmed=profile.confirmed,
    )


def get_or_create_story_profile(db: Session, book_id: int) -> StoryProfileDetail | None:
    book = db.scalar(select(Book).where(Book.id == book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None

    profile = db.scalar(select(StoryProfile).where(StoryProfile.book_id == book_id))
    if profile is None:
        chapters = db.scalars(
            select(Chapter)
            .where(Chapter.book_id == book_id, Chapter.is_deleted.is_(False))
            .order_by(Chapter.chapter_index)
        ).all()
        profile = build_initial_story_profile(book, list(chapters))
        book.story_profile_status = "generated"
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return serialize_story_profile(profile)


def update_story_profile(
    db: Session, book_id: int, payload: StoryProfileUpdate
) -> StoryProfileDetail | None:
    book = db.scalar(select(Book).where(Book.id == book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None

    profile = db.scalar(select(StoryProfile).where(StoryProfile.book_id == book_id))
    if profile is None:
        chapters = db.scalars(
            select(Chapter)
            .where(Chapter.book_id == book_id, Chapter.is_deleted.is_(False))
            .order_by(Chapter.chapter_index)
        ).all()
        profile = build_initial_story_profile(book, list(chapters))
        db.add(profile)
        db.flush()

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("confirmed") is None:
        update_data.pop("confirmed", None)
    for field_name, value in update_data.items():
        setattr(profile, field_name, value)

    profile.version += 1
    book.story_profile_status = "confirmed" if profile.confirmed else "generated"
    db.commit()
    db.refresh(profile)
    return serialize_story_profile(profile)
