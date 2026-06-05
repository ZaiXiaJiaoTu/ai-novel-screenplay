import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.story_profile import StoryProfile
from app.schemas.story_profile_schema import StoryProfileDetail, StoryProfileUpdate
from app.services.llm_service import LlmServiceError, call_llm_for_task


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


def build_story_profile_variables(book: Book, chapters: list[Chapter]) -> dict:
    return {
        "book_title": book.title,
        "novel_type": book.novel_type,
        "chapters": [
            {
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "content": chapter.content[:3000],
            }
            for chapter in chapters
        ],
    }


def parse_story_profile_response(response_text: str) -> dict | None:
    stripped = response_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = yaml.safe_load(stripped)
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def apply_story_profile_payload(profile: StoryProfile, payload: dict) -> None:
    for field_name in [
        "title",
        "genre",
        "overview",
        "world_setting",
        "main_conflict",
        "characters",
        "relationships",
        "key_events",
        "chapter_outlines",
        "clues",
        "tone",
        "locked_settings",
    ]:
        if field_name in payload:
            setattr(profile, field_name, payload[field_name])


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


def generate_story_profile(db: Session, book_id: int) -> StoryProfileDetail | None:
    book = db.scalar(select(Book).where(Book.id == book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None

    chapters = db.scalars(
        select(Chapter)
        .where(Chapter.book_id == book_id, Chapter.is_deleted.is_(False))
        .order_by(Chapter.chapter_index)
    ).all()
    profile = db.scalar(select(StoryProfile).where(StoryProfile.book_id == book_id))
    if profile is None:
        profile = build_initial_story_profile(book, list(chapters))
        db.add(profile)
        db.flush()

    try:
        response_text = call_llm_for_task(
            db,
            task_type="story_profile_generation",
            variables=build_story_profile_variables(book, list(chapters)),
        )
        parsed_payload = parse_story_profile_response(response_text)
        if parsed_payload:
            apply_story_profile_payload(profile, parsed_payload)
            profile.version += 1
            profile.confirmed = False
            book.story_profile_status = "generated"
        else:
            book.story_profile_status = "failed"
            profile.overview = profile.overview or "故事设定档案生成失败，请手动完善。"
    except LlmServiceError:
        book.story_profile_status = "generated"
    except Exception:
        book.story_profile_status = "failed"
        profile.overview = profile.overview or "故事设定档案生成失败，请手动完善。"

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
