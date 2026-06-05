from types import SimpleNamespace

import yaml

from app.models.generation_task import GenerationTask
from app.services.script_task_service import build_placeholder_generation, get_task_progress


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
