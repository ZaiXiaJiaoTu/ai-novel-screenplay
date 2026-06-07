"""LLM output validation, fact dedup, and episode business-rule checks.

Kept in a dedicated module to avoid bloating ``script_adaptation_service.py``.
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from app.models.script_adaptation import ScriptPlotEvent


# ── constants ───────────────────────────────────────────────────────────────

SEMANTIC_DEDUP_THRESHOLD: float = 0.82
"""SequenceMatcher ratio above which two facts are considered duplicates."""

STATE_CHANGE_SIGNAL_WORDS: frozenset[str] = frozenset({
    "突破", "晋升", "觉醒", "获得", "失去", "死亡", "重伤", "痊愈",
    "离开", "加入", "成为", "不再是", "解除", "恢复", "变异",
    "进化", "升级", "转变", "背叛", "和解", "决裂", "到达",
    "进入", "退出",
})

CHANGEABLE_FACT_TYPES: frozenset[str] = frozenset({
    "当前状态", "关系", "立场", "能力", "目标", "身份",
})

SENTENCE_FINAL_CLEANUP = re.compile(r"[的了吧吗呢啊呀哦嗯哎哟呵嘛哪哦哟]$")
REPEATED_CHAR_CLEANUP = re.compile(r"(.)\1{2,}")
PUNCTUATION_SPACE = re.compile(r"[\s，,。；;：:、！!？?\"\"''（）()]+")
N_GRAM_N = 3


# ── dataclasses ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str | None = None


# ── fact text normalization ─────────────────────────────────────────────────

def normalize_fact_content(value: str) -> str:
    """Enhanced normalization: punctuation/space removal + cleanup.

    This is the *first layer* — exact match after normalization.
    Still exported for use in ``merge_characters`` and tests.
    """
    text = value.strip().lower()
    text = SENTENCE_FINAL_CLEANUP.sub("", text)
    text = PUNCTUATION_SPACE.sub("", text)
    # Collapse 3+ repeated chars — rare CJK issue but harmless
    text = REPEATED_CHAR_CLEANUP.sub(r"\1\1", text)
    return text[:500]


# ── semantic dedup ──────────────────────────────────────────────────────────

def _char_ngrams(text: str, n: int = N_GRAM_N) -> set[str]:
    """Character n-grams for Jaccard-like comparison on Chinese text."""
    if len(text) < n:
        return {text}
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _jaccard_similarity(a: str, b: str) -> float:
    set_a = _char_ngrams(a)
    set_b = _char_ngrams(b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def is_semantically_duplicate_fact(
    new_content: str,
    existing_contents: list[str],
    *,
    threshold: float = SEMANTIC_DEDUP_THRESHOLD,
) -> bool:
    """Return True when *new_content* is semantically equivalent to
    any item in *existing_contents*.

    Uses a combination of character n-gram Jaccard and SequenceMatcher.
    Only a *high* similarity triggers a duplicate flag to avoid
    accidentally deleting genuine state-change facts.
    """
    if not existing_contents:
        return False
    norm_new = normalize_fact_content(new_content)
    if not norm_new:
        return False
    for existing in existing_contents:
        norm_existing = normalize_fact_content(existing)
        if not norm_existing:
            continue
        if norm_new == norm_existing:
            return True
        # Combined score: max of Jaccard and SequenceMatcher
        jaccard = _jaccard_similarity(norm_new, norm_existing)
        if jaccard >= threshold:
            return True
        seq_ratio = SequenceMatcher(None, norm_new, norm_existing).ratio()
        if seq_ratio >= threshold:
            return True
        # Combined lower threshold: both moderate = likely duplicate
        if jaccard >= 0.72 and seq_ratio >= 0.72:
            return True
    return False


def has_state_change_indicator(new_content: str, old_content: str) -> bool:
    """Return True when *new_content* appears to signal a state change
    relative to *old_content*, as opposed to being a near-duplicate.
    """
    norm_new = normalize_fact_content(new_content)
    norm_old = normalize_fact_content(old_content)
    if norm_new == norm_old:
        return False
    for word in STATE_CHANGE_SIGNAL_WORDS:
        if word in new_content and word not in old_content:
            return True
    return False


# ── episode business validation ─────────────────────────────────────────────

def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _scene_characters_set(scene: dict) -> set[str]:
    characters = scene.get("characters")
    if not isinstance(characters, list):
        return set()
    return {str(c).strip() for c in characters if str(c).strip()}


def validate_episode_payload(
    payload: dict,
    *,
    events: list[ScriptPlotEvent],
    episode_number: int,
    book_title: str,
) -> list[ValidationIssue]:
    """Run business-rule checks on a parsed episode YAML payload.

    Returns a list of ``ValidationIssue``; an empty list means the payload
    passes all checks.  The caller is responsible for deciding whether
    to auto-repair or fall back.
    """
    issues: list[ValidationIssue] = []

    # ── top-level structure ─────────────────────────────────────────────
    script = payload.get("script")
    if not isinstance(script, dict):
        issues.append(ValidationIssue("MISSING_SCRIPT", "缺少 script 顶层字段"))
        return issues

    metadata = script.get("metadata")
    scenes = script.get("scenes")
    if not isinstance(metadata, dict):
        issues.append(ValidationIssue("MISSING_METADATA", "缺少 script.metadata"))
    if not isinstance(scenes, list) or len(scenes) == 0:
        issues.append(ValidationIssue("MISSING_OR_EMPTY_SCENES", "scenes 为空或缺失"))
        return issues

    # ── metadata checks ────────────────────────────────────────────────
    if metadata:
        meta_ep_num = _safe_int(metadata.get("episode_number"))
        if meta_ep_num is not None and meta_ep_num != episode_number:
            issues.append(
                ValidationIssue(
                    "WRONG_EPISODE_NUMBER",
                    f"metadata.episode_number 应为 {episode_number}，实际为 {meta_ep_num}",
                    "script.metadata.episode_number",
                )
            )
        meta_book = str(metadata.get("source_book_title") or "").strip()
        if meta_book and meta_book != book_title:
            issues.append(
                ValidationIssue(
                    "WRONG_BOOK_TITLE",
                    f"source_book_title 应为 {book_title}，实际为 {meta_book}",
                    "script.metadata.source_book_title",
                )
            )
        title = str(metadata.get("title") or "").strip()
        if not title:
            issues.append(
                ValidationIssue(
                    "EMPTY_TITLE",
                    "标题为空",
                    "script.metadata.title",
                )
            )

    # ── scene checks ───────────────────────────────────────────────────
    valid_event_indices = {event.event_index for event in events}
    covered_events: set[int] = set()
    dialogue_speakers_all: set[str] = set()

    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            issues.append(
                ValidationIssue(
                    "INVALID_SCENE_ITEM",
                    f"scenes[{i}] 不是有效对象",
                    f"script.scenes[{i}]",
                )
            )
            continue
        scene_path = f"script.scenes[{i}]"

        # scene_id
        scene_id = _safe_int(scene.get("scene_id"))
        if scene_id is None:
            issues.append(
                ValidationIssue(
                    "MISSING_SCENE_ID",
                    f"场景 {i} 缺少 scene_id",
                    f"{scene_path}.scene_id",
                )
            )
        elif scene_id != i + 1:
            issues.append(
                ValidationIssue(
                    "NON_CONSECUTIVE_SCENE_ID",
                    f"scene_id 应为 {i + 1}，实际为 {scene_id}",
                    f"{scene_path}.scene_id",
                )
            )

        # source_events
        source_events = scene.get("source_events")
        if not isinstance(source_events, list) or len(source_events) == 0:
            issues.append(
                ValidationIssue(
                    "MISSING_SOURCE_EVENTS",
                    f"场景 {i} 缺少 source_events",
                    f"{scene_path}.source_events",
                )
            )
        else:
            for j, ev_ref in enumerate(source_events):
                ev_idx = _safe_int(ev_ref)
                if ev_idx is None:
                    issues.append(
                        ValidationIssue(
                            "INVALID_EVENT_REF",
                            f"source_events[{j}] 不是有效整数: {ev_ref}",
                            f"{scene_path}.source_events[{j}]",
                        )
                    )
                elif ev_idx not in valid_event_indices:
                    issues.append(
                        ValidationIssue(
                            "UNKNOWN_EVENT_INDEX",
                            f"事件编号 {ev_idx} 不在本集输入事件中",
                            f"{scene_path}.source_events[{j}]",
                        )
                    )
                else:
                    covered_events.add(ev_idx)

        # characters
        scene_chars = _scene_characters_set(scene)
        dialogue_speakers_all.update(
            str(c).strip() for c in scene.get("characters", []) if isinstance(c, str) and c.strip()
        )

        # action — just check for existence
        action = scene.get("action")
        if not action and action != "":
            issues.append(
                ValidationIssue(
                    "MISSING_ACTION",
                    f"场景 {i} 缺少 action",
                    f"{scene_path}.action",
                )
            )

        # dialogue
        dialogue = scene.get("dialogue")
        if isinstance(dialogue, list):
            for k, d_item in enumerate(dialogue):
                if not isinstance(d_item, dict):
                    issues.append(
                        ValidationIssue(
                            "INVALID_DIALOGUE_ITEM",
                            f"dialogue[{k}] 不是对象",
                            f"{scene_path}.dialogue[{k}]",
                        )
                    )
                    continue
                speaker = str(d_item.get("speaker") or "").strip()
                line = str(d_item.get("line") or "").strip()
                if not speaker:
                    issues.append(
                        ValidationIssue(
                            "MISSING_SPEAKER",
                            f"dialogue[{k}] 缺少 speaker",
                            f"{scene_path}.dialogue[{k}].speaker",
                        )
                    )
                if not line:
                    issues.append(
                        ValidationIssue(
                            "MISSING_LINE",
                            f"dialogue[{k}] 缺少 line",
                            f"{scene_path}.dialogue[{k}].line",
                        )
                    )
                if speaker and scene_chars and speaker not in scene_chars:
                    issues.append(
                        ValidationIssue(
                            "SPEAKER_NOT_IN_SCENE",
                            f"对白说话人 '{speaker}' 不在场景人物列表中",
                            f"{scene_path}.dialogue[{k}].speaker",
                        )
                    )

    # event coverage
    uncovered = valid_event_indices - covered_events
    if uncovered:
        issues.append(
            ValidationIssue(
                "EVENTS_NOT_COVERED",
                f"以下事件未被任何场景覆盖: {sorted(uncovered)}",
            )
        )

    return issues
