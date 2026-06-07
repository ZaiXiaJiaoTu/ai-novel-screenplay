"""Tests for the generate→validate→repair→revalidate→fallback pipeline."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.script_adaptation_service import (
    generate_one_episode,
)
from app.services.llm_service import LlmServiceError


# ── helpers ────────────────────────────────────────────────────────────────


def _make_event(event_id: int, event_index: int) -> MagicMock:
    return MagicMock(
        id=event_id,
        batch_id=1,
        event_index=event_index,
        content=f"事件{event_index}",
        source_chapter_start=1,
        source_chapter_end=1,
        locked=False,
    )


def _make_project() -> MagicMock:
    return MagicMock(
        id=1,
        book_id=1,
        script_type="short_drama",
        default_target_duration=5,
        pacing="fast",
        scene_frequency="high",
        dialogue_density="medium",
        events_per_episode=3,
        yaml_schema_delta={
            "metadata": {"format": "short_drama_episode", "hook_required": True},
            "scene_extra": ["hook", "cliffhanger"],
        },
        generation_status="idle",
        generation_stop_requested=False,
        split_stop_requested=False,
    )


def _valid_episode_yaml() -> str:
    return """script:
  metadata:
    title: 启程
    episode_number: 1
    source_book_title: 测试小说
  scenes:
    - scene_id: 1
      scene_title: 场景一
      source_events: [1]
      location: ""
      time: ""
      characters: ["唐三"]
      action:
        - 唐三走进房间。
      dialogue:
        - speaker: 唐三
          line: 来了。
      transition: ""
    - scene_id: 2
      scene_title: 场景二
      source_events: [2]
      location: ""
      time: ""
      characters: ["小舞"]
      action:
        - 小舞回头。
      dialogue: []
      transition: ""
    - scene_id: 3
      scene_title: 场景三
      source_events: [3]
      location: ""
      time: ""
      characters: ["唐三", "小舞"]
      action:
        - 两人对视。
      dialogue: []
      transition: ""
"""


def _broken_yaml() -> str:
    """YAML that parses but fails business validation.

    Uses correct book_title so it passes the off-topic guard,
    but has wrong episode_number, non-consecutive scene_id,
    unknown event_index, missing title, and speaker not in scene.
    """
    return """script:
  metadata:
    title: ""
    episode_number: 99
    source_book_title: 测试小说
  scenes:
    - scene_id: 5
      scene_title: 场景
      source_events: [999]
      location: ""
      time: ""
      characters: ["唐三"]
      action:
        - something
      dialogue:
        - speaker: 戴沐白
          line: 我来也。
      transition: ""
"""


def _setup_mocks(db: MagicMock, project: MagicMock, events: list[MagicMock]):
    """Set up mock DB and helper functions for generate_one_episode."""
    db.execute.return_value.first.return_value = (project, "测试小说")

    # mock get_available_events via scalars().all()
    db.scalars.return_value.all.return_value = events

    # max episode index
    db.scalar.return_value = 0

    # db.refresh should assign an id to the episode
    def _refresh(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 1

    db.refresh.side_effect = _refresh
    db.add.return_value = None
    db.flush.return_value = None


def _mock_characters_and_chapters():
    """Return an ExitStack of patches for get_characters and get_event_source_chapters."""
    import contextlib
    stack = contextlib.ExitStack()
    char_mock = MagicMock()
    char_mock.model_dump.return_value = {
        "character_id": 1, "name": "唐三", "profile": "唐三，主角。",
        "metadata_json": {},
    }
    chapter = SimpleNamespace(
        chapter_index=1, title="第一章", content="测试内容。",
    )
    stack.enter_context(patch(
        "app.services.script_adaptation_service.get_characters",
        return_value=[char_mock],
    ))
    stack.enter_context(patch(
        "app.services.script_adaptation_service.get_event_source_chapters",
        return_value=[chapter],
    ))
    return stack


# ── scenario 1: successful generation, no repair needed ────────────────────


def test_generate_valid_yaml_no_repair_needed():
    """Normal generation produces valid YAML -> saved as completed."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        return_value=_valid_episode_yaml(),
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert result is not None
    assert result.status == "completed"


# ── scenario 2: broken YAML repaired successfully ──────────────────────────


def test_broken_yaml_repaired_once_then_saved():
    """First call returns broken YAML, repair returns valid -> saved as completed."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    call_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        call_count[0] += 1
        if task_type == "script_episode_generation":
            return _broken_yaml()
        return _valid_episode_yaml()

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert call_count[0] == 2  # generate + repair
    assert result is not None
    assert result.status == "completed"


# ── scenario 3: both generate and repair fail -> fallback ───────────────────


def test_generate_and_repair_both_fail_uses_fallback():
    """Both generation and repair produce broken YAML -> fallback used."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    call_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        call_count[0] += 1
        return _broken_yaml()

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert call_count[0] == 2  # generate + one repair
    assert result is not None
    assert result.status == "fallback"


# ── scenario 4: YAML parse error -> repair -> success ────────────────────────


def test_unparseable_yaml_repaired_to_valid():
    """First call returns unparseable text, repair returns valid YAML."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    call_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        call_count[0] += 1
        if task_type == "script_episode_generation":
            return "not valid yaml at all {{{"
        return _valid_episode_yaml()

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert call_count[0] == 2
    assert result is not None
    assert result.status == "completed"


# ── scenario 5: LLM error on generate -> fallback directly ──────────────────


def test_llm_error_on_generate_falls_back_after_repair_attempt():
    """Both generate and repair throw LlmServiceError → fallback, 2 calls."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    call_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        call_count[0] += 1
        raise LlmServiceError("API error")

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert call_count[0] == 2  # generate + repair attempt (both fail)
    assert result is not None
    assert result.status == "fallback"


# ── scenario 6: LLM error on repair -> fallback ─────────────────────────────


def test_llm_error_on_repair_falls_back():
    """Generation produces broken YAML, repair throws -> fallback."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    call_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        call_count[0] += 1
        if task_type == "script_episode_generation":
            return _broken_yaml()
        raise LlmServiceError("repair failed")

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert call_count[0] == 2
    assert result is not None
    assert result.status == "fallback"


# ── scenario 7: repair called at most once ─────────────────────────────────


def test_repair_never_called_twice():
    """Even if repair output still has issues, repair is not called again."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    gen_count = [0]
    repair_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        if task_type == "script_episode_generation":
            gen_count[0] += 1
            return _broken_yaml()
        repair_count[0] += 1
        return _broken_yaml()

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    assert gen_count[0] == 1
    assert repair_count[0] == 1  # only once
    assert result.status == "fallback"


# ── scenario 8: off-topic detection bypasses repair ────────────────────────


def test_off_topic_repair_also_fails_then_fallback():
    """Off-topic generation → repair also off-topic → fallback, 2 calls."""
    project = _make_project()
    events = [_make_event(100 + i, i) for i in range(1, 4)]
    db = MagicMock()
    _setup_mocks(db, project, events)

    call_count = [0]

    def mock_llm(db_arg, *, task_type, variables):
        call_count[0] += 1
        return """script:
  metadata:
    title: test
  scenes:
    - scene_id: 1
      scene_title: test
      source_events: [1]
      location: 霍格沃茨
      time: ""
      characters: []
      action: []
      dialogue: []
      transition: ""
"""

    with patch(
        "app.services.script_adaptation_service.call_llm_for_task",
        side_effect=mock_llm,
    ):
        with _mock_characters_and_chapters():
            result = generate_one_episode(db, project.id)

    # Both generate and repair produce off-topic content → fallback
    assert call_count[0] == 2
    assert result.status == "fallback"
