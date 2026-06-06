from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.schemas.book_schema import (
    BookCreateResult,
    BookDetail,
    BookListItem,
    BookListResult,
    ChapterListItem,
)
from app.utils.chapter_parser import detect_novel_type, parse_chapters


def create_book_from_text(
    db: Session,
    *,
    title: str,
    content: str,
    source_type: str = "text",
    original_filename: str | None = None,
) -> BookCreateResult:
    title = title.strip()
    if not title:
        raise ValueError("作品名称不能为空")

    chapters = parse_chapters(content)
    if not chapters:
        raise ValueError("小说内容不能为空")

    word_count = sum(chapter.word_count for chapter in chapters)
    novel_type = detect_novel_type(word_count, len(chapters))
    book = Book(
        title=title,
        original_filename=original_filename,
        source_type=source_type,
        novel_type=novel_type,
        word_count=word_count,
        chapter_count=len(chapters),
        preprocess_status="completed",
    )
    db.add(book)
    db.flush()

    db.add_all(
        [
            Chapter(
                book_id=book.id,
                chapter_index=chapter.chapter_index,
                title=chapter.title,
                content=chapter.content,
                word_count=chapter.word_count,
            )
            for chapter in chapters
        ]
    )
    db.commit()
    db.refresh(book)
    return BookCreateResult(
        book_id=book.id,
        title=book.title,
        preprocess_status=book.preprocess_status,
    )


def list_books(
    db: Session,
    *,
    keyword: str | None = None,
    novel_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> BookListResult:
    stmt: Select[tuple[Book]] = select(Book).where(Book.is_deleted.is_(False))
    count_stmt = select(func.count()).select_from(Book).where(Book.is_deleted.is_(False))

    if keyword:
        keyword_like = f"%{keyword.strip()}%"
        stmt = stmt.where(Book.title.ilike(keyword_like))
        count_stmt = count_stmt.where(Book.title.ilike(keyword_like))
    if novel_type:
        stmt = stmt.where(Book.novel_type == novel_type)
        count_stmt = count_stmt.where(Book.novel_type == novel_type)

    page = max(page, 1)
    size = min(max(size, 1), 100)
    books = db.scalars(
        stmt.order_by(Book.created_at.desc()).offset((page - 1) * size).limit(size)
    ).all()
    total = db.scalar(count_stmt) or 0
    return BookListResult(
        records=[
            BookListItem(
                book_id=book.id,
                title=book.title,
                novel_type=book.novel_type,
                chapter_count=book.chapter_count,
                word_count=book.word_count,
                preprocess_status=book.preprocess_status,
            )
            for book in books
        ],
        total=total,
    )


def get_book_detail(db: Session, book_id: int) -> BookDetail | None:
    book = db.scalar(select(Book).where(Book.id == book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None
    return BookDetail(
        book_id=book.id,
        title=book.title,
        novel_type=book.novel_type,
        chapter_count=book.chapter_count,
        word_count=book.word_count,
        preprocess_status=book.preprocess_status,
    )


def list_book_chapters(db: Session, book_id: int) -> list[ChapterListItem] | None:
    exists = db.scalar(select(Book.id).where(Book.id == book_id, Book.is_deleted.is_(False)))
    if exists is None:
        return None
    chapters = db.scalars(
        select(Chapter)
        .where(Chapter.book_id == book_id, Chapter.is_deleted.is_(False))
        .order_by(Chapter.chapter_index)
    ).all()
    return [
        ChapterListItem(
            chapter_id=chapter.id,
            chapter_index=chapter.chapter_index,
            title=chapter.title,
            word_count=chapter.word_count,
        )
        for chapter in chapters
    ]
