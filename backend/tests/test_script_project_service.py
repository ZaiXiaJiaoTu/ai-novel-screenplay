from types import SimpleNamespace

from app.services.script_project_service import serialize_segment


def test_serialize_segment_maps_content_fields():
    segment = SimpleNamespace(
        id=1,
        project_id=2,
        book_id=3,
        segment_name="第1章剧本",
        adapt_scope={"type": "single_chapter", "chapter": 1},
        style="校园悬疑",
        compression_level="high",
        target_duration=5,
        scene_count=1,
        yaml_content="script: {}",
        plain_text_content="剧本文本",
        status="completed",
    )

    result = serialize_segment(segment)

    assert result.segment_id == 1
    assert result.project_id == 2
    assert result.yaml_content == "script: {}"
    assert result.status == "completed"
