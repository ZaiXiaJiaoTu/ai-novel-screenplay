import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.chapter_summary import ChapterSummary
from app.schemas.chapter_summary_schema import (
    ChapterDetail,
    ChapterSummaryDetail,
    ChapterSummaryGenerationResult,
)
from app.services.llm_service import LlmServiceError, call_llm_for_task


CHAPTER_SUMMARY_FIELDS = [
    "characters",
    "key_events",
    "locations",
    "clues",
    "emotion_changes",
]


def parse_chapter_summary_response(response_text: str) -> dict | None:
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


def build_chapter_summary_variables(book: Book, chapter: Chapter) -> dict:
    return {
        "book_title": book.title,
        "novel_type": book.novel_type,
        "chapter_index": chapter.chapter_index,
        "chapter_title": chapter.title,
        "chapter_content": chapter.content[:6000],
    }


def build_fallback_chapter_summary(chapter: Chapter) -> dict:
    content = " ".join(chapter.content.split())
    summary = content[:300] if content else chapter.title
    return {
        "summary": summary,
        "characters": [],
        "key_events": [],
        "locations": [],
        "clues": [],
        "emotion_changes": [],
    }


def normalize_chapter_summary_payload(payload: dict | None, chapter: Chapter) -> dict:
    if not payload:
        payload = build_fallback_chapter_summary(chapter)

    normalized = build_fallback_chapter_summary(chapter)
    if isinstance(payload.get("summary"), str) and payload["summary"].strip():
        normalized["summary"] = payload["summary"].strip()

    for field_name in CHAPTER_SUMMARY_FIELDS:
        value = payload.get(field_name)
        normalized[field_name] = value if isinstance(value, list) else []
    return normalized


def serialize_chapter(chapter: Chapter) -> ChapterDetail:
    return ChapterDetail(
        chapter_id=chapter.id,
        book_id=chapter.book_id,
        chapter_index=chapter.chapter_index,
        title=chapter.title,
        content=chapter.content,
        word_count=chapter.word_count,
    )


def serialize_chapter_summary(summary: ChapterSummary) -> ChapterSummaryDetail:
    return ChapterSummaryDetail(
        summary_id=summary.id,
        book_id=summary.book_id,
        chapter_id=summary.chapter_id,
        chapter_index=summary.chapter.chapter_index,
        chapter_title=summary.chapter.title,
        summary=summary.summary,
        characters=summary.characters or [],
        key_events=summary.key_events or [],
        locations=summary.locations or [],
        clues=summary.clues or [],
        emotion_changes=summary.emotion_changes or [],
    )


def get_chapter_detail(db: Session, chapter_id: int) -> ChapterDetail | None:
    chapter = db.scalar(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.is_deleted.is_(False))
    )
    return serialize_chapter(chapter) if chapter else None


def get_chapter_summary(db: Session, chapter_id: int) -> ChapterSummaryDetail | None:
    summary = db.scalar(
        select(ChapterSummary)
        .join(Chapter)
        .where(
            ChapterSummary.chapter_id == chapter_id,
            Chapter.is_deleted.is_(False),
        )
    )
    return serialize_chapter_summary(summary) if summary else None


def upsert_chapter_summary(
    db: Session, book: Book, chapter: Chapter, payload: dict
) -> ChapterSummary:
    summary = db.scalar(
        select(ChapterSummary).where(ChapterSummary.chapter_id == chapter.id)
    )
    if summary is None:
        summary = ChapterSummary(book_id=book.id, chapter_id=chapter.id)
        db.add(summary)

    summary.summary = payload["summary"]
    summary.characters = payload["characters"]
    summary.key_events = payload["key_events"]
    summary.locations = payload["locations"]
    summary.clues = payload["clues"]
    summary.emotion_changes = payload["emotion_changes"]
    return summary


def generate_chapter_summaries(
    db: Session, book_id: int
) -> ChapterSummaryGenerationResult | None:
    book = db.scalar(select(Book).where(Book.id == book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None

    chapters = db.scalars(
        select(Chapter)
        .where(Chapter.book_id == book_id, Chapter.is_deleted.is_(False))
        .order_by(Chapter.chapter_index)
    ).all()

    summaries: list[ChapterSummary] = []
    for chapter in chapters:
        try:
            response_text = call_llm_for_task(
                db,
                task_type="chapter_summary_generation",
                variables=build_chapter_summary_variables(book, chapter),
            )
            parsed_payload = parse_chapter_summary_response(response_text)
        except LlmServiceError:
            parsed_payload = None
        except Exception:
            parsed_payload = None

        payload = normalize_chapter_summary_payload(parsed_payload, chapter)
        summaries.append(upsert_chapter_summary(db, book, chapter, payload))

    book.preprocess_status = "completed"
    db.commit()
    for summary in summaries:
        db.refresh(summary)

    return ChapterSummaryGenerationResult(
        book_id=book.id,
        generated_count=len(summaries),
        summaries=[serialize_chapter_summary(summary) for summary in summaries],
    )
