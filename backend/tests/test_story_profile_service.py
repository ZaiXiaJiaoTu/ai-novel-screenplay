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


def test_parse_story_profile_response_accepts_json_fence():
    from app.services.story_profile_service import parse_story_profile_response

    response = """```json
{"title": "长夜来信", "characters": []}
```"""

    parsed = parse_story_profile_response(response)

    assert parsed == {"title": "长夜来信", "characters": []}


def test_apply_story_profile_payload_updates_known_fields():
    from app.services.story_profile_service import apply_story_profile_payload

    profile = SimpleNamespace(title="", characters=[])

    apply_story_profile_payload(profile, {"title": "长夜来信", "characters": ["林川"], "x": 1})

    assert profile.title == "长夜来信"
    assert profile.characters == ["林川"]
    assert not hasattr(profile, "x")


def test_build_story_profile_variables_truncates_chapter_content():
    from app.services.story_profile_service import build_story_profile_variables

    book = SimpleNamespace(title="长夜来信", novel_type="short")
    chapters = [SimpleNamespace(chapter_index=1, title="第1章", content="x" * 4000)]

    variables = build_story_profile_variables(book, chapters)

    assert variables["book_title"] == "长夜来信"
    assert len(variables["chapters"][0]["content"]) == 3000
