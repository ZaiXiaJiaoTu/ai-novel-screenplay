import yaml

from app.services.demo_seed_service import (
    DEMO_BOOK_TITLE,
    DEMO_CHAPTERS,
    DEMO_SUMMARIES,
    build_demo_plain_text,
    build_demo_script_payload,
    build_demo_seed_preview,
)


def test_demo_seed_preview_has_complete_demo_flow():
    preview = build_demo_seed_preview()

    assert preview["book_title"] == DEMO_BOOK_TITLE
    assert preview["chapter_count"] == 3
    assert preview["summary_count"] == 3
    assert preview["script_scene_count"] == 3


def test_demo_chapters_and_summaries_stay_aligned():
    assert len(DEMO_CHAPTERS) == len(DEMO_SUMMARIES)
    assert all(chapter["title"] for chapter in DEMO_CHAPTERS)
    assert all(summary["summary"] for summary in DEMO_SUMMARIES)


def test_demo_script_yaml_is_parseable():
    preview = build_demo_seed_preview(book_id=12)
    parsed = yaml.safe_load(preview["script_yaml"])

    assert parsed["script"]["metadata"]["source_book_id"] == "12"
    assert parsed["script"]["metadata"]["script_type"] == "short_drama"
    assert len(parsed["script"]["scenes"]) == 3


def test_demo_plain_text_contains_scene_dialogue():
    payload = build_demo_script_payload(book_id=1)
    plain_text = build_demo_plain_text(payload)

    assert "第一集：旧楼来信" in plain_text
    assert "S1. 雨夜回楼" in plain_text
    assert "林夏：" in plain_text
