from types import SimpleNamespace

from app.schemas.story_profile_schema import StoryProfileUpdate
from app.services.story_profile_service import build_initial_story_profile


def test_build_initial_story_profile_from_book_and_chapters():
    book = SimpleNamespace(id=1, title="长夜来信", novel_type="short")
    chapters = [
        SimpleNamespace(chapter_index=1, title="第1章 旧信"),
        SimpleNamespace(chapter_index=2, title="第2章 旧楼"),
    ]

    profile = build_initial_story_profile(book, chapters)

    assert profile.book_id == 1
    assert profile.title == "长夜来信"
    assert profile.genre == "short"
    assert profile.version == 1
    assert profile.confirmed is False
    assert profile.chapter_outlines == [
        {"chapter_index": 1, "title": "第1章 旧信", "summary": ""},
        {"chapter_index": 2, "title": "第2章 旧楼", "summary": ""},
    ]


def test_story_profile_update_accepts_partial_payload():
    payload = StoryProfileUpdate(overview="新的故事简介")

    assert payload.model_dump(exclude_unset=True) == {"overview": "新的故事简介"}
