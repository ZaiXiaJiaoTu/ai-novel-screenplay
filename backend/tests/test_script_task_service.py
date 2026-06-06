from datetime import datetime
from types import SimpleNamespace

import yaml

from app.models.generation_task import GenerationTask
from app.services.script_task_service import (
    build_script_plain_text,
    build_placeholder_generation,
    build_generation_outputs,
    get_task_progress,
    parse_script_yaml_response,
    save_generated_script_to_shelf,
    serialize_task_list_item,
    strip_markdown_code_fence,
    sync_script_yaml_artifact_to_segment,
)


def test_build_placeholder_generation_contains_yaml():
    book = SimpleNamespace(id=1, title="长夜来信")
    chapters = [SimpleNamespace(chapter_index=1, title="第1章 旧信")]
    task = SimpleNamespace(
        id=10,
        script_project_id=None,
        adapt_scope={"type": "single_chapter", "chapter": 1},
        generation_config={
            "script_type": "short_drama",
            "style": "校园悬疑",
            "compression_level": "high",
            "target_duration": 5,
        },
    )

    generated = build_placeholder_generation(book, chapters, task)
    parsed = yaml.safe_load(generated["script_yaml"]["yaml"])

    assert generated["style_strategy"]["style"] == "校园悬疑"
    assert parsed["script"]["metadata"]["source_book_id"] == "1"
    assert parsed["script"]["scenes"][0]["source_chapters"] == [1]


def test_task_progress_uses_status_and_step():
    task = GenerationTask(status="running", current_step="scene_planning")
    assert get_task_progress(task) == 50

    task.status = "completed"
    assert get_task_progress(task) == 100


def test_serialize_task_list_item_includes_book_title_and_progress():
    task = GenerationTask(
        id=8,
        book_id=3,
        script_project_id=5,
        status="running",
        current_step="script_yaml",
        created_at=datetime(2026, 6, 6),
    )

    result = serialize_task_list_item(task, "夜雨旧楼")

    assert result.task_id == 8
    assert result.book_id == 3
    assert result.book_title == "夜雨旧楼"
    assert result.script_project_id == 5
    assert result.progress == 80


def test_parse_script_yaml_response_accepts_markdown_fence():
    response = """```yaml
script:
  metadata:
    title: 长夜来信
  scenes: []
```"""

    parsed = parse_script_yaml_response(response)

    assert parsed is not None
    assert parsed["structured"]["script"]["metadata"]["title"] == "长夜来信"
    assert strip_markdown_code_fence(response).startswith("script:")


def test_build_script_plain_text_uses_segment_and_scene_titles():
    payload = {
        "script": {
            "metadata": {"segment_title": "第一集"},
            "scenes": [
                {"scene_id": "S1", "scene_title": "雨夜"},
                {"scene_id": "S2", "scene_title": "旧楼"},
            ],
        }
    }

    assert build_script_plain_text(payload) == "第一集\nS1. 雨夜\nS2. 旧楼"


def test_build_generation_outputs_falls_back_without_llm_config():
    book = SimpleNamespace(id=1, title="长夜来信")
    chapters = [SimpleNamespace(chapter_index=1, title="第1章 旧信", content="正文")]
    task = SimpleNamespace(
        id=10,
        script_project_id=None,
        adapt_scope={"type": "single_chapter", "chapter": 1},
        generation_config={"style": "校园悬疑", "target_duration": 5},
    )

    generated = build_generation_outputs(SimpleNamespace(), book, chapters, task)

    assert generated["style_strategy"]["source"] == "placeholder"
    assert generated["scene_plan"]["source"] == "placeholder"
    assert generated["script_yaml"]["source"] == "placeholder"


def test_build_generation_outputs_uses_llm_when_available():
    book = SimpleNamespace(id=1, title="长夜来信")
    chapters = [SimpleNamespace(chapter_index=1, title="第1章 旧信", content="正文")]
    task = SimpleNamespace(
        id=10,
        script_project_id=None,
        adapt_scope={"type": "single_chapter", "chapter": 1},
        generation_config={"style": "校园悬疑", "target_duration": 5},
    )

    def fake_call_llm(_db, *, task_type, variables, task_id):
        assert variables["book_title"] == "长夜来信"
        assert task_id == 10
        if task_type == "script_yaml_generation":
            return "script:\n  metadata:\n    title: LLM剧本\n  scenes: []\n"
        return f"{task_type} result"

    import app.services.script_task_service as service

    old_call = service.call_llm_for_task
    service.call_llm_for_task = fake_call_llm
    try:
        generated = service.build_generation_outputs(SimpleNamespace(), book, chapters, task)
    finally:
        service.call_llm_for_task = old_call

    assert generated["style_strategy"]["source"] == "llm"
    assert generated["scene_plan"]["source"] == "llm"
    assert generated["script_yaml"]["source"] == "llm"
    assert generated["script_yaml"]["structured"]["script"]["metadata"]["title"] == "LLM剧本"


def test_save_generated_script_to_shelf_adds_project_and_segment():
    class FakeDb:
        def __init__(self):
            self.objects = []

        def scalar(self, _stmt):
            return None

        def add(self, obj):
            self.objects.append(obj)

        def flush(self):
            self.objects[-1].id = 20

    db = FakeDb()
    book = SimpleNamespace(id=1, title="长夜来信")
    task = SimpleNamespace(
        id=10,
        script_project_id=None,
        adapt_scope={"type": "single_chapter", "chapter": 1},
        generation_config={"style": "校园悬疑", "target_duration": 5},
    )
    generated = build_placeholder_generation(
        book,
        [SimpleNamespace(chapter_index=1, title="第1章 旧信")],
        task,
    )

    segment = save_generated_script_to_shelf(
        db,
        task=task,
        book=book,
        generated=generated,
    )

    assert task.script_project_id == 20
    assert segment.project_id == 20
    assert segment.book_id == 1
    assert segment.status == "completed"
    assert "script:" in segment.yaml_content


def test_sync_script_yaml_artifact_to_segment_updates_latest_segment():
    class FakeDb:
        def __init__(self, task, segment):
            self.task = task
            self.segment = segment
            self.scalar_calls = 0

        def scalar(self, _stmt):
            self.scalar_calls += 1
            return self.task if self.scalar_calls == 1 else self.segment

    task = SimpleNamespace(id=10, script_project_id=20)
    segment = SimpleNamespace(
        segment_name="旧名称",
        yaml_content="",
        plain_text_content="",
        scene_count=0,
        actual_word_count=0,
    )
    artifact = SimpleNamespace(
        artifact_type="script_yaml",
        task_id=10,
        content={
            "structured": {
                "script": {
                    "metadata": {"segment_title": "新版片段"},
                    "scenes": [{"scene_id": "S1", "scene_title": "新场景"}],
                }
            }
        },
    )

    sync_script_yaml_artifact_to_segment(FakeDb(task, segment), artifact)

    assert segment.segment_name == "新版片段"
    assert "script:" in segment.yaml_content
    assert segment.plain_text_content == "新版片段\nS1. 新场景"
    assert segment.scene_count == 1
    assert segment.actual_word_count > 0
