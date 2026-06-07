"""Tests for llm_output_validation_service: fact dedup and episode validation."""

from types import SimpleNamespace

import pytest

from app.services.llm_output_validation_service import (
    SEMANTIC_DEDUP_THRESHOLD,
    ValidationIssue,
    has_state_change_indicator,
    is_semantically_duplicate_fact,
    normalize_fact_content,
    validate_episode_payload,
)


# ── normalize_fact_content ──────────────────────────────────────────────


def test_normalize_removes_punctuation_and_space():
    assert normalize_fact_content("唐三之母，十万年蓝银皇。") == normalize_fact_content(
        "唐三之母 十万年蓝银皇"
    )


def test_normalize_strips_sentence_final_particles():
    """P0.4: Sentence-final particles are removed to improve dedup."""
    result = normalize_fact_content("他是很厉害的")
    assert result == "他是很厉害"


def test_normalize_collapses_repeated_chars():
    result = normalize_fact_content("啊啊啊啊啊啊")
    assert len(result) <= 3


def test_normalize_is_case_insensitive():
    assert normalize_fact_content("HELLO") == normalize_fact_content("hello")


# ── is_semantically_duplicate_fact ──────────────────────────────────────


def test_exact_normalized_match_is_duplicate():
    assert is_semantically_duplicate_fact(
        "唐三拥有蓝银草武魂。",
        ["唐三拥有蓝银草武魂"],
    ) is True


def test_punctuation_variants_are_duplicate():
    assert is_semantically_duplicate_fact(
        "唐三之母，十万年蓝银皇。",
        ["唐三之母 十万年蓝银皇"],
    ) is True


def test_high_similarity_is_duplicate():
    """Near-identical facts with minor rewording are caught."""
    assert is_semantically_duplicate_fact(
        "唐三的武魂是蓝银草，先天满魂力",
        ["唐三武魂为蓝银草，拥有先天满魂力"],
    ) is True


def test_distinct_facts_are_not_duplicate():
    assert is_semantically_duplicate_fact(
        "唐三前往诺丁城求学",
        ["小舞是十万年魂兽化形"],
    ) is False


def test_empty_existing_contents_returns_false():
    assert is_semantically_duplicate_fact("唐三觉醒武魂", []) is False


def test_empty_new_content_returns_false():
    assert is_semantically_duplicate_fact("   ", ["any content"]) is False


def test_threshold_is_configurable():
    """A very low threshold should match moderately similar strings."""
    assert is_semantically_duplicate_fact(
        "唐三前往诺丁城学习",
        ["唐三去诺丁城求学"],
        threshold=0.01,
    ) is True


# ── has_state_change_indicator ──────────────────────────────────────────


def test_state_change_detected_when_old_lacks_signal_word():
    assert has_state_change_indicator("唐三突破至魂尊境界", "唐三为魂师") is True


def test_state_change_when_new_has_unique_signal_word():
    """Signal word in new but not in old → state change."""
    assert has_state_change_indicator("唐三觉醒蓝银皇血脉", "唐三为魂师") is True


def test_no_state_change_when_same_signal_in_both():
    """Same signal word in both old and new → no unique indicator."""
    assert has_state_change_indicator("唐三突破至魂尊", "唐三已突破至魂宗") is False


def test_no_state_change_when_identical():
    assert has_state_change_indicator("唐三为魂师", "唐三为魂师") is False


# ── validate_episode_payload ────────────────────────────────────────────


def _make_events(*indices: int) -> list:
    return [
        SimpleNamespace(id=100 + idx, event_index=idx, content=f"事件{idx}")
        for idx in indices
    ]


def _valid_payload(events: list | None = None) -> dict:
    if events is None:
        events = _make_events(1, 2)
    return {
        "script": {
            "metadata": {
                "title": "测试标题",
                "episode_number": 1,
                "source_book_title": "测试小说",
            },
            "scenes": [
                {
                    "scene_id": 1,
                    "scene_title": "场景一",
                    "source_events": [1],
                    "location": "",
                    "time": "",
                    "characters": ["唐三"],
                    "action": ["唐三走进房间。"],
                    "dialogue": [
                        {"speaker": "唐三", "line": "我来了。"},
                    ],
                    "transition": "",
                },
                {
                    "scene_id": 2,
                    "scene_title": "场景二",
                    "source_events": [2],
                    "location": "",
                    "time": "",
                    "characters": ["小舞"],
                    "action": ["小舞回头。"],
                    "dialogue": [],
                    "transition": "",
                },
            ],
        }
    }


def test_valid_payload_passes_all_checks():
    events = _make_events(1, 2)
    issues = validate_episode_payload(
        _valid_payload(events),
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert issues == []


def test_missing_script_top_level():
    issues = validate_episode_payload(
        {},
        events=_make_events(1),
        episode_number=1,
        book_title="书",
    )
    assert any(i.code == "MISSING_SCRIPT" for i in issues)


def test_missing_metadata_and_empty_scenes():
    issues = validate_episode_payload(
        {"script": {}},
        events=_make_events(1),
        episode_number=1,
        book_title="书",
    )
    codes = {i.code for i in issues}
    assert "MISSING_METADATA" in codes
    assert "MISSING_OR_EMPTY_SCENES" in codes


def test_wrong_episode_number():
    payload = _valid_payload(_make_events(1))
    issues = validate_episode_payload(
        payload,
        events=_make_events(1),
        episode_number=5,
        book_title="测试小说",
    )
    assert any(i.code == "WRONG_EPISODE_NUMBER" for i in issues)


def test_wrong_book_title():
    payload = _valid_payload(_make_events(1))
    issues = validate_episode_payload(
        payload,
        events=_make_events(1),
        episode_number=1,
        book_title="正确书名",
    )
    assert any(i.code == "WRONG_BOOK_TITLE" for i in issues)


def test_non_consecutive_scene_ids():
    events = _make_events(1, 2)
    payload = _valid_payload(events)
    payload["script"]["scenes"][1]["scene_id"] = 5
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "NON_CONSECUTIVE_SCENE_ID" for i in issues)


def test_unknown_event_index_in_source_events():
    events = _make_events(1)
    payload = _valid_payload(events)
    payload["script"]["scenes"][1]["scene_id"] = 2
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "UNKNOWN_EVENT_INDEX" for i in issues)


def test_event_not_covered():
    events = _make_events(1, 2, 3)
    payload = _valid_payload(events)
    # Remove scene that covers event 2
    payload["script"]["scenes"] = [payload["script"]["scenes"][0]]
    # Fix scene_id
    payload["script"]["scenes"][0]["scene_id"] = 1
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "EVENTS_NOT_COVERED" for i in issues)


def test_dialogue_speaker_missing():
    events = _make_events(1, 2)
    payload = _valid_payload(events)
    payload["script"]["scenes"][0]["dialogue"] = [
        {"line": "缺少speaker"},
    ]
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "MISSING_SPEAKER" for i in issues)


def test_dialogue_speaker_not_in_scene_characters():
    events = _make_events(1, 2)
    payload = _valid_payload(events)
    payload["script"]["scenes"][0]["dialogue"] = [
        {"speaker": "戴沐白", "line": "我来也。"},
    ]
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "SPEAKER_NOT_IN_SCENE" for i in issues)


def test_empty_title_detected():
    events = _make_events(1)
    payload = _valid_payload(events)
    payload["script"]["metadata"]["title"] = ""
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "EMPTY_TITLE" for i in issues)


def test_dialogue_line_missing():
    events = _make_events(1)
    payload = _valid_payload(events)
    payload["script"]["scenes"][0]["dialogue"] = [
        {"speaker": "唐三"},
    ]
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "MISSING_LINE" for i in issues)


def test_invalid_scene_item_is_reported():
    events = _make_events(1)
    payload = _valid_payload(events)
    payload["script"]["scenes"].append("not_a_dict")
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="测试小说",
    )
    assert any(i.code == "INVALID_SCENE_ITEM" for i in issues)


def test_all_events_covered_passes():
    events = _make_events(1, 2, 3)
    payload = {
        "script": {
            "metadata": {"title": "全覆盖", "episode_number": 1, "source_book_title": "书"},
            "scenes": [
                {
                    "scene_id": 1, "scene_title": "S1",
                    "source_events": [1, 2, 3],
                    "location": "", "time": "",
                    "characters": ["唐三"],
                    "action": ["事件"], "dialogue": [], "transition": "",
                },
            ],
        }
    }
    issues = validate_episode_payload(
        payload,
        events=events,
        episode_number=1,
        book_title="书",
    )
    # Should have no EVENT coverage issues
    assert not any(i.code == "EVENTS_NOT_COVERED" for i in issues)
    assert issues == []


# ── ValidationIssue ─────────────────────────────────────────────────────


def test_validation_issue_is_hashable():
    issue = ValidationIssue("CODE", "message", "path")
    assert {issue, issue}  # won't raise
