from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.schemas.chapter_schema import (
    ChapterCreate,
    ChapterDeleteResult,
    ChapterDetail,
    ChapterUpdate,
)
from app.utils.chapter_parser import count_words, detect_novel_type


def normalize_chapter_index(requested_index: int | None, chapter_count: int) -> int:
    if requested_index is None:
        return chapter_count + 1
    return min(max(requested_index, 1), chapter_count + 1)


def serialize_chapter(chapter: Chapter) -> ChapterDetail:
    return ChapterDetail(
        chapter_id=chapter.id,
        book_id=chapter.book_id,
        chapter_index=chapter.chapter_index,
        title=chapter.title,
        content=chapter.content,
        word_count=chapter.word_count,
    )


def get_chapter_detail(db: Session, chapter_id: int) -> ChapterDetail | None:
    chapter = db.scalar(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.is_deleted.is_(False))
    )
    return serialize_chapter(chapter) if chapter else None


def _get_active_book(db: Session, book_id: int) -> Book | None:
    return db.scalar(select(Book).where(Book.id == book_id, Book.is_deleted.is_(False)))


def _get_active_chapter(db: Session, chapter_id: int) -> Chapter | None:
    return db.scalar(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.is_deleted.is_(False))
    )


def _list_active_chapters(db: Session, book_id: int) -> list[Chapter]:
    return list(
        db.scalars(
            select(Chapter)
            .where(Chapter.book_id == book_id, Chapter.is_deleted.is_(False))
            .order_by(Chapter.chapter_index, Chapter.id)
        ).all()
    )


def refresh_book_stats(db: Session, book: Book) -> None:
    chapters = _list_active_chapters(db, book.id)
    total_words = 0
    for index, chapter in enumerate(chapters, start=1):
        chapter.chapter_index = index
        total_words += chapter.word_count
    book.chapter_count = len(chapters)
    book.word_count = total_words
    book.novel_type = detect_novel_type(total_words, len(chapters))


def create_chapter(
    db: Session, book_id: int, payload: ChapterCreate
) -> ChapterDetail | None:
    book = _get_active_book(db, book_id)
    if book is None:
        return None

    chapters = _list_active_chapters(db, book_id)
    insert_index = normalize_chapter_index(payload.chapter_index, len(chapters))
    for chapter in chapters:
        if chapter.chapter_index >= insert_index:
            chapter.chapter_index += 1

    chapter = Chapter(
        book_id=book_id,
        chapter_index=insert_index,
        title=payload.title.strip(),
        content=payload.content,
        word_count=count_words(payload.content),
    )
    db.add(chapter)
    db.flush()
    refresh_book_stats(db, book)
    db.commit()
    db.refresh(chapter)
    return serialize_chapter(chapter)


def update_chapter(
    db: Session, chapter_id: int, payload: ChapterUpdate
) -> ChapterDetail | None:
    chapter = _get_active_chapter(db, chapter_id)
    if chapter is None:
        return None

    if payload.title is not None:
        chapter.title = payload.title.strip()
    if payload.content is not None:
        chapter.content = payload.content
        chapter.word_count = count_words(payload.content)

    book = _get_active_book(db, chapter.book_id)
    if book is not None:
        refresh_book_stats(db, book)
    db.commit()
    db.refresh(chapter)
    return serialize_chapter(chapter)


def delete_chapter(db: Session, chapter_id: int) -> ChapterDeleteResult | None:
    chapter = _get_active_chapter(db, chapter_id)
    if chapter is None:
        return None

    chapter.is_deleted = True
    book = _get_active_book(db, chapter.book_id)
    if book is not None:
        refresh_book_stats(db, book)
    db.commit()
    return ChapterDeleteResult(chapter_id=chapter_id, deleted=True)
