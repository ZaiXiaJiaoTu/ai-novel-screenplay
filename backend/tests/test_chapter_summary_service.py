from types import SimpleNamespace

from app.services.chapter_summary_service import (
    build_chapter_summary_variables,
    build_fallback_chapter_summary,
    normalize_chapter_summary_payload,
    parse_chapter_summary_response,
    serialize_chapter,
)


def test_parse_chapter_summary_response_accepts_json_fence():
    response = """```json
{"summary": "主角发现线索", "characters": ["林川"]}
```"""

    parsed = parse_chapter_summary_response(response)

    assert parsed == {"summary": "主角发现线索", "characters": ["林川"]}


def test_normalize_chapter_summary_payload_defaults_missing_lists():
    chapter = SimpleNamespace(title="第一章", content="林川回到旧楼。")

    payload = normalize_chapter_summary_payload({"summary": "旧楼重逢"}, chapter)

    assert payload["summary"] == "旧楼重逢"
    assert payload["characters"] == []
    assert payload["key_events"] == []


def test_build_fallback_chapter_summary_uses_content_excerpt():
    chapter = SimpleNamespace(title="第一章", content="  林川   回到旧楼。  ")

    payload = build_fallback_chapter_summary(chapter)

    assert payload["summary"] == "林川 回到旧楼。"
    assert payload["locations"] == []


def test_build_chapter_summary_variables_truncates_chapter_content():
    book = SimpleNamespace(title="长夜来信", novel_type="short")
    chapter = SimpleNamespace(chapter_index=1, title="第一章", content="x" * 7000)

    variables = build_chapter_summary_variables(book, chapter)

    assert variables["book_title"] == "长夜来信"
    assert len(variables["chapter_content"]) == 6000


def test_serialize_chapter_maps_content_fields():
    chapter = SimpleNamespace(
        id=1,
        book_id=2,
        chapter_index=3,
        title="第三章",
        content="正文",
        word_count=2,
    )

    result = serialize_chapter(chapter)

    assert result.chapter_id == 1
    assert result.content == "正文"
