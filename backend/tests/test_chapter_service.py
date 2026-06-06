from types import SimpleNamespace

from app.services.chapter_service import normalize_chapter_index, serialize_chapter


def test_normalize_chapter_index_appends_by_default():
    assert normalize_chapter_index(None, 3) == 4


def test_normalize_chapter_index_clamps_to_existing_bounds():
    assert normalize_chapter_index(0, 3) == 1
    assert normalize_chapter_index(99, 3) == 4


def test_serialize_chapter_returns_editable_content():
    chapter = SimpleNamespace(
        id=7,
        book_id=3,
        chapter_index=2,
        title="Chapter 2",
        content="正文内容",
        word_count=12,
    )

    result = serialize_chapter(chapter)

    assert result.chapter_id == 7
    assert result.book_id == 3
    assert result.content == "正文内容"
