import json
import re
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.export_record import ExportRecord
from app.models.script_adaptation import (
    ScriptCharacterFact,
    ScriptCharacterProfile,
    ScriptEpisode,
    ScriptEventBatch,
    ScriptPlotEvent,
)
from app.models.script_project import ScriptProject
from app.schemas.script_adaptation_schema import (
    ScriptAdaptationConfigUpdate,
    ScriptAdaptationCreate,
    ScriptAdaptationProject,
    ScriptAdaptationProjectList,
    ScriptCharacterDetail,
    ScriptCharacterUpdate,
    ScriptEpisodeDetail,
    ScriptEpisodeGeneratePayload,
    ScriptEpisodeUpdate,
    ScriptEventBatchDetail,
    ScriptExportResult,
    ScriptPlotEventDetail,
    ScriptPlotEventUpdate,
    ScriptWorkflowProgress,
)
from app.services.llm_output_validation_service import (
    is_semantically_duplicate_fact,
    normalize_fact_content,
    validate_episode_payload,
)
from app.services.llm_service import LlmServiceError, call_llm_for_task
from app.utils.chapter_parser import count_words


TYPE_LABELS = {
    "tv": "电视剧",
    "short_drama": "短剧",
    "animation": "动画",
    "audio_drama": "广播剧",
}
PACING_LABELS = {"fast": "快", "medium": "适中", "slow": "慢"}
LEVEL_LABELS = {"high": "高", "medium": "中", "low": "低"}
CHAPTERS_PER_BATCH = 3
OFF_TOPIC_MARKERS = [
    "哈利波特",
    "霍格沃茨",
    "格兰芬多",
    "斯莱特林",
    "Harry Potter",
    "Hogwarts",
    "Gryffindor",
    "Slytherin",
]


def get_yaml_schema_delta(adaptation_type: str) -> dict:
    base = {
        "required": ["script.metadata", "script.scenes"],
        "scene_required": [
            "scene_id",
            "scene_title",
            "source_events",
            "location",
            "time",
            "characters",
            "action",
            "dialogue",
            "transition",
        ],
    }
    type_delta = {
        "tv": {
            "metadata": {"format": "episode", "act_structure": "teaser/acts/tag"},
            "scene_extra": ["act", "subplot_hint"],
        },
        "short_drama": {
            "metadata": {"format": "short_drama_episode", "hook_required": True},
            "scene_extra": ["hook", "cliffhanger"],
        },
        "animation": {
            "metadata": {"format": "animation_episode"},
            "scene_extra": ["visual_action", "sound_effects"],
        },
        "audio_drama": {
            "metadata": {"format": "audio_drama_episode"},
            "scene_extra": ["soundscape", "voice_direction"],
        },
    }
    return {**base, **type_delta[adaptation_type]}


def build_adaptation_config(project: ScriptProject) -> dict:
    """Build adaptation config with derived explicit targets.

    Converts fuzzy pacing/scene_frequency/dialogue_density labels into
    concrete numeric ranges so the model has precise guidance.
    """
    config: dict = {
        "adaptation_type": project.script_type,
        "adaptation_type_label": TYPE_LABELS.get(project.script_type or "", project.script_type),
        "episode_duration": project.default_target_duration,
        "pacing": project.pacing,
        "pacing_label": PACING_LABELS.get(project.pacing, project.pacing),
        "scene_frequency": project.scene_frequency,
        "scene_frequency_label": LEVEL_LABELS.get(project.scene_frequency, project.scene_frequency),
        "dialogue_density": project.dialogue_density,
        "dialogue_density_label": LEVEL_LABELS.get(project.dialogue_density, project.dialogue_density),
        "events_per_episode": project.events_per_episode,
        "yaml_schema_delta": project.yaml_schema_delta or get_yaml_schema_delta(project.script_type or "short_drama"),
    }
    # ── derived explicit targets ───────────────────────────────────────
    config.update(_derive_adaptation_targets(config))
    return config


def _derive_adaptation_targets(config: dict) -> dict:
    """Compute concrete numeric targets from fuzzy labels.

    These give the model explicit guardrails without hard-coding values
    into the prompt templates themselves.
    """
    duration = int(config.get("episode_duration") or 5)
    pacing = str(config.get("pacing") or "medium")
    scene_freq = str(config.get("scene_frequency") or "medium")
    dialogue_density = str(config.get("dialogue_density") or "medium")
    events_per = int(config.get("events_per_episode") or 5)

    # target_scene_count derived from events × scene frequency
    scene_multiplier = {"high": 1.5, "medium": 1.0, "low": 0.7}
    multiplier = scene_multiplier.get(scene_freq, 1.0)
    center = max(2, round(events_per * multiplier))
    target_scene_count = {"min": max(1, center - 2), "max": center + 2}

    # dialogue_ratio from dialogue_density label
    dialogue_ranges = {
        "high": (0.45, 0.65),
        "medium": (0.30, 0.50),
        "low": (0.15, 0.35),
    }
    d_min, d_max = dialogue_ranges.get(dialogue_density, (0.25, 0.50))
    dialogue_ratio = {"min": d_min, "max": d_max}

    # scene_length_hint from pacing + duration
    if duration <= 3:
        scene_length_hint = "极短"
    elif duration <= 7:
        scene_length_hint = "短" if pacing == "fast" else "适中"
    elif duration <= 15:
        scene_length_hint = "适中" if pacing != "slow" else "较长"
    else:
        scene_length_hint = "较长"

    # ending_requirement from adaptation type
    adaptation_type = str(config.get("adaptation_type") or "short_drama")
    ending_map = {
        "short_drama": "形成悬念或情绪转折",
        "tv": "设置下一集内容钩子",
        "animation": "形成段落收束或悬念",
        "audio_drama": "形成听觉收束或悬念",
    }
    ending_requirement = ending_map.get(adaptation_type, "形成悬念或情绪转折")

    return {
        "target_scene_count": target_scene_count,
        "dialogue_ratio": dialogue_ratio,
        "scene_length_hint": scene_length_hint,
        "ending_requirement": ending_requirement,
    }


# ── relevant character selection ──────────────────────────────────────────

def select_relevant_characters(
    characters: list[ScriptCharacterDetail],
    events: list[ScriptPlotEvent],
    chapters: list[Chapter],
    *,
    max_characters: int = 30,
) -> list[ScriptCharacterDetail]:
    """Return only characters relevant to the given events and chapters.

    Relevance rules:
    1. Character name appears in event content.
    2. Character name appears in chapter content.
    3. Any alias (from metadata_json) appears in event or chapter content.
    4. Always include a small number of core characters if the result set
       is below *max_characters*.
    """
    if not characters:
        return []

    # Build the search corpus from event content and chapter content
    corpus_parts: list[str] = []
    for event in events:
        corpus_parts.append(event.content)
    for chapter in chapters:
        corpus_parts.append(chapter.title)
        corpus_parts.append(chapter.content or "")

    corpus = "\n".join(corpus_parts)

    # Normalise corpus for case-insensitive matching
    corpus_lower = corpus.lower()

    def _is_relevant(character: ScriptCharacterDetail) -> bool:
        name = (character.name or "").strip()
        if not name:
            return False
        if name.lower() in corpus_lower:
            return True
        # Check aliases from metadata_json
        metadata = character.metadata_json or {}
        aliases: list[str] = metadata.get("aliases") or []
        for alias in aliases:
            alias_str = str(alias).strip()
            if alias_str and alias_str.lower() in corpus_lower:
                return True
        return False

    relevant = [c for c in characters if _is_relevant(c)]

    # If no characters matched at all, include a few core characters
    if not relevant and characters:
        relevant = characters[: min(3, len(characters))]

    # Cap at max_characters
    return relevant[:max_characters]


def parse_json_payload(response_text: str) -> dict | None:
    stripped = response_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def list_project_chapters(db: Session, project: ScriptProject) -> list[Chapter]:
    return list(
        db.scalars(
            select(Chapter)
            .where(Chapter.book_id == project.book_id, Chapter.is_deleted.is_(False))
            .order_by(Chapter.chapter_index)
        ).all()
    )


def serialize_event(event: ScriptPlotEvent) -> ScriptPlotEventDetail:
    return ScriptPlotEventDetail(
        event_id=event.id,
        batch_id=event.batch_id,
        event_index=event.event_index,
        content=event.content,
        source_chapter_start=event.source_chapter_start,
        source_chapter_end=event.source_chapter_end,
        locked=event.locked,
    )


def serialize_character(character: ScriptCharacterProfile) -> ScriptCharacterDetail:
    metadata = character.metadata_json or {}
    consolidated_profile = metadata.get("consolidated_profile")
    facts = getattr(character, "active_facts", None)
    profile = character.profile
    if consolidated_profile:
        profile = str(consolidated_profile)
    elif facts:
        profile = "\n".join(f"{index}. {fact.content}" for index, fact in enumerate(facts, start=1))
    return ScriptCharacterDetail(
        character_id=character.id,
        name=character.name,
        profile=profile,
        metadata_json=character.metadata_json,
    )


def serialize_episode(episode: ScriptEpisode) -> ScriptEpisodeDetail:
    return ScriptEpisodeDetail(
        episode_id=episode.id,
        episode_index=episode.episode_index,
        title=episode.title,
        event_ids=[int(item) for item in episode.event_ids],
        yaml_content=episode.yaml_content,
        yaml_payload=parse_episode_yaml_content(episode.yaml_content),
        plain_text_content=episode.plain_text_content,
        status=episode.status,
    )


def get_project_counts(db: Session, project_id: int) -> tuple[int, int, int]:
    event_count = db.scalar(
        select(func.count())
        .select_from(ScriptPlotEvent)
        .where(ScriptPlotEvent.project_id == project_id, ScriptPlotEvent.is_deleted.is_(False))
    ) or 0
    character_count = db.scalar(
        select(func.count())
        .select_from(ScriptCharacterProfile)
        .where(
            ScriptCharacterProfile.project_id == project_id,
            ScriptCharacterProfile.is_deleted.is_(False),
        )
    ) or 0
    episode_count = db.scalar(
        select(func.count())
        .select_from(ScriptEpisode)
        .where(ScriptEpisode.project_id == project_id, ScriptEpisode.is_deleted.is_(False))
    ) or 0
    return event_count, character_count, episode_count


def serialize_project(
    db: Session, project: ScriptProject, book_title: str
) -> ScriptAdaptationProject:
    event_count, character_count, episode_count = get_project_counts(db, project.id)
    return ScriptAdaptationProject(
        project_id=project.id,
        book_id=project.book_id,
        book_title=book_title,
        project_name=project.project_name,
        adaptation_type=project.script_type or "short_drama",
        episode_duration=project.default_target_duration,
        pacing=project.pacing,
        scene_frequency=project.scene_frequency,
        dialogue_density=project.dialogue_density,
        events_per_episode=project.events_per_episode,
        yaml_schema_delta=project.yaml_schema_delta,
        split_status=project.split_status,
        split_stop_requested=project.split_stop_requested,
        generation_status=project.generation_status,
        generation_stop_requested=project.generation_stop_requested,
        event_count=event_count,
        character_count=character_count,
        episode_count=episode_count,
    )


def list_adaptation_projects(
    db: Session, *, page: int = 1, size: int = 20
) -> ScriptAdaptationProjectList:
    stmt = (
        select(ScriptProject, Book.title)
        .join(Book, Book.id == ScriptProject.book_id)
        .where(ScriptProject.is_deleted.is_(False), Book.is_deleted.is_(False))
    )
    total = db.scalar(
        select(func.count()).select_from(ScriptProject).where(ScriptProject.is_deleted.is_(False))
    ) or 0
    rows = db.execute(
        stmt.order_by(ScriptProject.created_at.desc(), ScriptProject.id.desc())
        .offset((max(page, 1) - 1) * min(max(size, 1), 100))
        .limit(min(max(size, 1), 100))
    ).all()
    return ScriptAdaptationProjectList(
        records=[serialize_project(db, project, book_title) for project, book_title in rows],
        total=total,
    )


def get_project_with_book(db: Session, project_id: int) -> tuple[ScriptProject, str] | None:
    row = db.execute(
        select(ScriptProject, Book.title)
        .join(Book, Book.id == ScriptProject.book_id)
        .where(
            ScriptProject.id == project_id,
            ScriptProject.is_deleted.is_(False),
            Book.is_deleted.is_(False),
        )
    ).first()
    return row if row else None


def create_adaptation_project(
    db: Session, payload: ScriptAdaptationCreate
) -> ScriptAdaptationProject | None:
    book = db.scalar(select(Book).where(Book.id == payload.book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None
    project = ScriptProject(
        book_id=book.id,
        project_name=payload.project_name.strip(),
        script_type=payload.adaptation_type,
        default_style=TYPE_LABELS[payload.adaptation_type],
        default_compression_level=payload.pacing,
        default_target_duration=payload.episode_duration,
        pacing=payload.pacing,
        scene_frequency=payload.scene_frequency,
        dialogue_density=payload.dialogue_density,
        events_per_episode=payload.events_per_episode,
        yaml_schema_delta=get_yaml_schema_delta(payload.adaptation_type),
        status="ongoing",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return serialize_project(db, project, book.title)


def update_adaptation_config(
    db: Session, project_id: int, payload: ScriptAdaptationConfigUpdate
) -> ScriptAdaptationProject | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, book_title = row
    data = payload.model_dump(exclude_unset=True)
    if "project_name" in data and data["project_name"] is not None:
        project.project_name = data["project_name"].strip()
    if "episode_duration" in data and data["episode_duration"] is not None:
        project.default_target_duration = data["episode_duration"]
    if "pacing" in data and data["pacing"] is not None:
        project.pacing = data["pacing"]
        project.default_compression_level = data["pacing"]
    if "scene_frequency" in data and data["scene_frequency"] is not None:
        project.scene_frequency = data["scene_frequency"]
    if "dialogue_density" in data and data["dialogue_density"] is not None:
        project.dialogue_density = data["dialogue_density"]
    if "events_per_episode" in data and data["events_per_episode"] is not None:
        project.events_per_episode = data["events_per_episode"]
    db.commit()
    db.refresh(project)
    return serialize_project(db, project, book_title)


def delete_adaptation_project(db: Session, project_id: int) -> bool | None:
    project = db.scalar(
        select(ScriptProject).where(
            ScriptProject.id == project_id, ScriptProject.is_deleted.is_(False)
        )
    )
    if project is None:
        return None
    project.is_deleted = True
    project.deleted_at = datetime.utcnow()
    for model in (ScriptPlotEvent, ScriptCharacterFact, ScriptCharacterProfile, ScriptEpisode):
        for item in db.scalars(
            select(model).where(model.project_id == project_id, model.is_deleted.is_(False))
        ):
            item.is_deleted = True
            item.deleted_at = datetime.utcnow()
    db.commit()
    return True


def get_next_split_chapters(
    db: Session, project: ScriptProject
) -> tuple[int, list[Chapter]] | None:
    chapters = list_project_chapters(db, project)
    done_batches = db.scalar(
        select(func.count())
        .select_from(ScriptEventBatch)
        .where(ScriptEventBatch.project_id == project.id)
    ) or 0
    start = done_batches * CHAPTERS_PER_BATCH
    if start >= len(chapters):
        return None
    return done_batches + 1, chapters[start : start + CHAPTERS_PER_BATCH]


def build_character_context(db: Session, project_id: int) -> list[dict]:
    characters = db.scalars(
        select(ScriptCharacterProfile)
        .where(
            ScriptCharacterProfile.project_id == project_id,
            ScriptCharacterProfile.is_deleted.is_(False),
        )
        .order_by(ScriptCharacterProfile.name)
    ).all()
    result: list[dict] = []
    for character in characters:
        facts = db.scalars(
            select(ScriptCharacterFact)
            .where(
                ScriptCharacterFact.character_id == character.id,
                ScriptCharacterFact.is_deleted.is_(False),
                ScriptCharacterFact.status == "active",
            )
            .order_by(ScriptCharacterFact.id)
        ).all()
        entry: dict = {
            "name": character.name,
            "facts": [
                {"fact_type": fact.fact_type, "content": fact.content}
                for fact in facts
            ],
        }
        # Include aliases from metadata_json if present (P1.2)
        metadata = character.metadata_json or {}
        aliases = metadata.get("aliases")
        if isinstance(aliases, list) and aliases:
            entry["aliases"] = [str(a).strip() for a in aliases if str(a).strip()]
        result.append(entry)
    return result


def build_split_variables(
    project: ScriptProject, book_title: str, chapters: list[Chapter], db: Session | None = None
) -> dict:
    return {
        "book_title": book_title,
        "adaptation_config": build_adaptation_config(project),
        "existing_characters": build_character_context(db, project.id) if db is not None else [],
        "chapters": [
            {
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "content": chapter.content[:5000],
            }
            for chapter in chapters
        ],
        "output_contract": {
            "events": [{"content": "简洁且准确的一段剧情事件", "source_chapter_start": 1, "source_chapter_end": 1}],
            "characters": [
                {
                    "name": "人物标准名称",
                    "facts": [
                        {
                            "fact_type": "关键特征/性格/能力/关系/当前状态",
                            "content": "只写本批章节带来的新增关键特征或状态变化，不写完整人物介绍",
                        }
                    ],
                }
            ],
        },
    }


def fallback_split_payload(chapters: list[Chapter]) -> dict:
    events = [
        {
            "content": f"{chapter.title}：{chapter.content[:160]}",
            "source_chapter_start": chapter.chapter_index,
            "source_chapter_end": chapter.chapter_index,
        }
        for chapter in chapters
    ]
    return {"events": events, "characters": []}


def normalize_split_payload(payload: dict | None, chapters: list[Chapter]) -> dict:
    fallback = fallback_split_payload(chapters)
    if not payload:
        return fallback
    events = payload.get("events")
    characters = payload.get("characters")
    if not isinstance(events, list) or not events:
        events = fallback["events"]
    if not isinstance(characters, list):
        characters = []
    return {"events": events, "characters": characters}


def normalize_character_facts_payload(item: dict) -> dict:
    """Normalize a character item from any format to the standard facts schema.

    Compatible input keys: traits, features, facts, profile, description.
    Output always uses ``facts`` with ``fact_type`` and ``content``.
    """
    result: dict = {"name": str(item.get("name") or "").strip()}
    raw_facts = item.get("traits") or item.get("features") or item.get("facts")
    if isinstance(raw_facts, list):
        normalized: list[dict] = []
        for fact in raw_facts:
            if isinstance(fact, str):
                normalized.append({"fact_type": "关键特征", "content": fact.strip()})
            elif isinstance(fact, dict):
                normalized.append(
                    {
                        "fact_type": str(
                            fact.get("trait_type")
                            or fact.get("feature_type")
                            or fact.get("fact_type")
                            or fact.get("type")
                            or "关键特征"
                        ),
                        "content": str(
                            fact.get("content")
                            or fact.get("trait")
                            or fact.get("feature")
                            or fact.get("fact")
                            or ""
                        ).strip(),
                    }
                )
        result["facts"] = normalized
    else:
        fallback = str(item.get("profile") or item.get("description") or "").strip()
        result["facts"] = [{"fact_type": "设定", "content": fallback}] if fallback else []
    return result


def extract_character_facts(item: dict) -> list[dict]:
    return normalize_character_facts_payload(item)["facts"]


def _merge_aliases_into_metadata(character: ScriptCharacterProfile, item: dict) -> None:
    """Merge aliases from an incoming character item into metadata_json (P1.2)."""
    incoming_aliases: list[str] = []
    raw_aliases = item.get("aliases")
    if isinstance(raw_aliases, list):
        incoming_aliases = [str(a).strip() for a in raw_aliases if str(a).strip()]

    metadata = dict(character.metadata_json or {})
    existing_aliases: list[str] = [
        str(a).strip()
        for a in (metadata.get("aliases") or [])
        if str(a).strip()
    ]

    # Merge without duplicates
    merged: list[str] = list(dict.fromkeys(existing_aliases + incoming_aliases))
    if merged:
        metadata["aliases"] = merged
    elif "aliases" in metadata:
        del metadata["aliases"]
    character.metadata_json = metadata


def rebuild_character_profile(db: Session, character: ScriptCharacterProfile) -> None:
    facts = db.scalars(
        select(ScriptCharacterFact)
        .where(
            ScriptCharacterFact.character_id == character.id,
            ScriptCharacterFact.is_deleted.is_(False),
            ScriptCharacterFact.status == "active",
        )
        .order_by(ScriptCharacterFact.id)
    ).all()
    character.profile = "\n".join(
        f"{index}. {fact.content}" for index, fact in enumerate(facts, start=1)
    )


def merge_characters(
    db: Session, project_id: int, characters: list[dict], batch_id: int | None = None
) -> None:
    existing_by_name: dict[str, ScriptCharacterProfile] = {}
    existing_aliases: dict[str, ScriptCharacterProfile] = {}
    for character in db.scalars(
        select(ScriptCharacterProfile).where(
            ScriptCharacterProfile.project_id == project_id,
            ScriptCharacterProfile.is_deleted.is_(False),
        )
    ):
        existing_by_name[character.name] = character
        metadata = character.metadata_json or {}
        for alias in metadata.get("aliases") or []:
            alias_str = str(alias).strip()
            if alias_str:
                existing_aliases[alias_str] = character

    for item in characters:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        # Match by name first, then by existing aliases
        if name in existing_by_name:
            character = existing_by_name[name]
        elif name in existing_aliases:
            character = existing_aliases[name]
        else:
            character = ScriptCharacterProfile(
                project_id=project_id,
                name=name,
                profile="",
                metadata_json=item,
            )
            db.add(character)
            db.flush()
            existing_by_name[name] = character
        # Merge aliases from new item into metadata_json
        _merge_aliases_into_metadata(character, item)
        existing_facts = {
            fact.normalized_content
            for fact in db.scalars(
                select(ScriptCharacterFact).where(
                    ScriptCharacterFact.character_id == character.id,
                    ScriptCharacterFact.is_deleted.is_(False),
                )
            )
        }
        existing_contents = [
            fact.content
            for fact in db.scalars(
                select(ScriptCharacterFact).where(
                    ScriptCharacterFact.character_id == character.id,
                    ScriptCharacterFact.is_deleted.is_(False),
                    ScriptCharacterFact.status == "active",
                )
            )
        ]
        for fact in extract_character_facts(item):
            content = fact["content"].strip()
            normalized = normalize_fact_content(content)
            if not content or not normalized:
                continue
            # Layer 1: exact dedup after normalization
            if normalized in existing_facts:
                continue
            # Layer 2: semantic dedup (n-gram Jaccard + SequenceMatcher)
            if is_semantically_duplicate_fact(content, existing_contents):
                continue
            db.add(
                ScriptCharacterFact(
                    project_id=project_id,
                    character_id=character.id,
                    batch_id=batch_id,
                    fact_type=fact["fact_type"][:100],
                    content=content,
                    normalized_content=normalized,
                    status="active",
                )
            )
            existing_facts.add(normalized)
            existing_contents.append(content)
        rebuild_character_profile(db, character)


def split_one_batch(
    db: Session, project_id: int, *, clear_stop_on_finish: bool = True
) -> ScriptWorkflowProgress | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, book_title = row
    next_batch = get_next_split_chapters(db, project)
    if next_batch is None:
        project.split_status = "completed"
        project.split_stop_requested = False
        db.commit()
        return get_progress(db, project_id)
    batch_index, chapters = next_batch
    project.split_status = "running"
    db.commit()

    if project.split_stop_requested:
        project.split_status = "stopped"
        if clear_stop_on_finish:
            project.split_stop_requested = False
        db.commit()
        return get_progress(db, project_id)

    variables = build_split_variables(project, book_title, chapters, db)
    parsed_payload = None
    try:
        response_text = call_llm_for_task(
            db,
            task_type="plot_event_split_generation",
            variables=variables,
        )
        parsed_payload = parse_json_payload(response_text)
    except LlmServiceError:
        parsed_payload = None
    db.refresh(project)
    payload = normalize_split_payload(parsed_payload, chapters)

    batch = ScriptEventBatch(
        project_id=project.id,
        book_id=project.book_id,
        batch_index=batch_index,
        chapter_start_index=chapters[0].chapter_index,
        chapter_end_index=chapters[-1].chapter_index,
        raw_response=payload,
    )
    db.add(batch)
    db.flush()

    current_max = db.scalar(
        select(func.max(ScriptPlotEvent.event_index)).where(
            ScriptPlotEvent.project_id == project.id
        )
    ) or 0
    for offset, item in enumerate(payload["events"], start=1):
        if isinstance(item, str):
            content = item
            start_chapter = chapters[0].chapter_index
            end_chapter = chapters[-1].chapter_index
        else:
            content = str(item.get("content") or item.get("event") or "").strip()
            start_chapter = int(item.get("source_chapter_start") or chapters[0].chapter_index)
            end_chapter = int(item.get("source_chapter_end") or chapters[-1].chapter_index)
        if content:
            db.add(
                ScriptPlotEvent(
                    project_id=project.id,
                    batch_id=batch.id,
                    event_index=current_max + offset,
                    content=content,
                    source_chapter_start=start_chapter,
                    source_chapter_end=end_chapter,
                )
            )
    merge_characters(db, project.id, payload["characters"], batch.id)
    project.split_status = "stopped" if project.split_stop_requested else "idle"
    if project.split_stop_requested and clear_stop_on_finish:
        project.split_stop_requested = False
    db.commit()
    return get_progress(db, project_id)


def run_split_all_batches(project_id: int) -> None:
    db = SessionLocal()
    try:
        row = get_project_with_book(db, project_id)
        if row is None:
            return
        project, _book_title = row
        while True:
            db.refresh(project)
            if project.split_stop_requested:
                project.split_status = "stopped"
                project.split_stop_requested = False
                db.commit()
                break
            if get_next_split_chapters(db, project) is None:
                project.split_status = "completed"
                db.commit()
                break
            split_one_batch(db, project_id, clear_stop_on_finish=False)
    finally:
        db.close()


def start_split_all_batches(db: Session, project_id: int) -> ScriptWorkflowProgress | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, _book_title = row
    project.split_stop_requested = False
    project.split_status = "running"
    db.commit()
    threading.Thread(target=run_split_all_batches, args=(project_id,), daemon=True).start()
    return get_progress(db, project_id)


def stop_split(db: Session, project_id: int) -> ScriptWorkflowProgress | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, _ = row
    project.split_stop_requested = True
    db.commit()
    return get_progress(db, project_id)


def get_batches(db: Session, project_id: int) -> list[ScriptEventBatchDetail] | None:
    if get_project_with_book(db, project_id) is None:
        return None
    rows = db.execute(
        select(ScriptEventBatch, func.count(ScriptPlotEvent.id))
        .outerjoin(
            ScriptPlotEvent,
            (ScriptPlotEvent.batch_id == ScriptEventBatch.id)
            & (ScriptPlotEvent.is_deleted.is_(False)),
        )
        .where(ScriptEventBatch.project_id == project_id)
        .group_by(ScriptEventBatch.id)
        .order_by(ScriptEventBatch.batch_index)
    ).all()
    return [
        ScriptEventBatchDetail(
            batch_id=batch.id,
            batch_index=batch.batch_index,
            chapter_start_index=batch.chapter_start_index,
            chapter_end_index=batch.chapter_end_index,
            status=batch.status,
            event_count=count,
        )
        for batch, count in rows
    ]


def get_events(db: Session, project_id: int) -> list[ScriptPlotEventDetail] | None:
    if get_project_with_book(db, project_id) is None:
        return None
    events = db.scalars(
        select(ScriptPlotEvent)
        .where(ScriptPlotEvent.project_id == project_id, ScriptPlotEvent.is_deleted.is_(False))
        .order_by(ScriptPlotEvent.event_index)
    ).all()
    return [serialize_event(event) for event in events]


def update_event(
    db: Session, event_id: int, payload: ScriptPlotEventUpdate
) -> ScriptPlotEventDetail | None:
    event = db.scalar(
        select(ScriptPlotEvent).where(
            ScriptPlotEvent.id == event_id, ScriptPlotEvent.is_deleted.is_(False)
        )
    )
    if event is None:
        return None
    if event.locked:
        raise ValueError("已用于剧集生成的剧情事件不可编辑")
    event.content = payload.content.strip()
    db.commit()
    db.refresh(event)
    return serialize_event(event)


def delete_event(db: Session, event_id: int) -> bool | None:
    event = db.scalar(
        select(ScriptPlotEvent).where(
            ScriptPlotEvent.id == event_id, ScriptPlotEvent.is_deleted.is_(False)
        )
    )
    if event is None:
        return None
    if event.locked:
        raise ValueError("已用于剧集生成的剧情事件不可删除")
    event.is_deleted = True
    event.deleted_at = datetime.utcnow()
    db.commit()
    return True


def get_characters(db: Session, project_id: int) -> list[ScriptCharacterDetail] | None:
    if get_project_with_book(db, project_id) is None:
        return None
    characters = db.scalars(
        select(ScriptCharacterProfile)
        .where(
            ScriptCharacterProfile.project_id == project_id,
            ScriptCharacterProfile.is_deleted.is_(False),
        )
        .order_by(ScriptCharacterProfile.name)
    ).all()
    for character in characters:
        character.active_facts = db.scalars(
            select(ScriptCharacterFact)
            .where(
                ScriptCharacterFact.character_id == character.id,
                ScriptCharacterFact.is_deleted.is_(False),
                ScriptCharacterFact.status == "active",
            )
            .order_by(ScriptCharacterFact.id)
        ).all()
    return [serialize_character(character) for character in characters]


def normalize_consolidated_character_payload(payload: dict | None) -> list[dict]:
    if not payload:
        return []
    characters = payload.get("characters")
    return characters if isinstance(characters, list) else []


def consolidate_character_profiles(db: Session, project_id: int) -> list[ScriptCharacterDetail] | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    _project, book_title = row
    characters = db.scalars(
        select(ScriptCharacterProfile)
        .where(
            ScriptCharacterProfile.project_id == project_id,
            ScriptCharacterProfile.is_deleted.is_(False),
        )
        .order_by(ScriptCharacterProfile.name)
    ).all()
    if not characters:
        return []
    variables = {
        "book_title": book_title,
        "characters": [
            {
                "name": character.name,
                "facts": [
                    {"fact_type": fact.fact_type, "content": fact.content}
                    for fact in db.scalars(
                        select(ScriptCharacterFact)
                        .where(
                            ScriptCharacterFact.character_id == character.id,
                            ScriptCharacterFact.is_deleted.is_(False),
                            ScriptCharacterFact.status == "active",
                        )
                        .order_by(ScriptCharacterFact.id)
                    )
                ],
            }
            for character in characters
        ],
    }
    parsed_payload = None
    try:
        response_text = call_llm_for_task(
            db,
            task_type="character_profile_consolidation",
            variables=variables,
        )
        parsed_payload = parse_json_payload(response_text)
    except LlmServiceError:
        parsed_payload = None

    by_name = {character.name: character for character in characters}
    updated = False
    for item in normalize_consolidated_character_payload(parsed_payload):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        profile = str(item.get("profile") or "").strip()
        if name in by_name and profile:
            by_name[name].profile = profile
            by_name[name].metadata_json = {
                **(by_name[name].metadata_json or {}),
                "consolidated_profile": profile,
            }
            updated = True
    if not updated:
        for character in characters:
            rebuild_character_profile(db, character)
    db.commit()
    return get_characters(db, project_id)


def update_character(
    db: Session, character_id: int, payload: ScriptCharacterUpdate
) -> ScriptCharacterDetail | None:
    character = db.scalar(
        select(ScriptCharacterProfile).where(
            ScriptCharacterProfile.id == character_id,
            ScriptCharacterProfile.is_deleted.is_(False),
        )
    )
    if character is None:
        return None
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        character.name = data["name"].strip()
    if "profile" in data and data["profile"] is not None:
        character.profile = data["profile"]
    if "metadata_json" in data:
        character.metadata_json = data["metadata_json"]
    db.commit()
    db.refresh(character)
    return serialize_character(character)


def get_available_events(db: Session, project_id: int, limit: int) -> list[ScriptPlotEvent]:
    return list(
        db.scalars(
            select(ScriptPlotEvent)
            .where(
                ScriptPlotEvent.project_id == project_id,
                ScriptPlotEvent.is_deleted.is_(False),
                ScriptPlotEvent.locked.is_(False),
            )
            .order_by(ScriptPlotEvent.event_index)
            .limit(limit)
        ).all()
    )


def get_event_source_chapters(
    db: Session, project: ScriptProject, events: list[ScriptPlotEvent]
) -> list[Chapter]:
    if not events:
        return []
    start = min(event.source_chapter_start for event in events)
    end = max(event.source_chapter_end for event in events)
    return list(
        db.scalars(
            select(Chapter)
            .where(
                Chapter.book_id == project.book_id,
                Chapter.is_deleted.is_(False),
                Chapter.chapter_index >= start,
                Chapter.chapter_index <= end,
            )
            .order_by(Chapter.chapter_index)
        ).all()
    )


def build_episode_variables(
    db: Session,
    project: ScriptProject,
    book_title: str,
    events: list[ScriptPlotEvent],
    episode_number: int,
) -> dict:
    all_characters = get_characters(db, project.id) or []
    chapters = get_event_source_chapters(db, project, events)
    # P1.1: only pass characters relevant to this episode's events + chapters
    relevant_characters = select_relevant_characters(
        all_characters,
        events,
        chapters,
    )
    return {
        "book_title": book_title,
        "adaptation_config": build_adaptation_config(project),
        "episode_number": episode_number,
        "events": [serialize_event(event).model_dump() for event in events],
        "characters": [character.model_dump() for character in relevant_characters],
        "chapters": [
            {
                "chapter_index": chapter.chapter_index,
                "title": chapter.title,
                "content": chapter.content[:5000],
            }
            for chapter in chapters
        ],
        "yaml_schema_delta": project.yaml_schema_delta,
    }


def parse_yaml_payload(response_text: str) -> dict | None:
    stripped = response_text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        parsed = yaml.safe_load(stripped)
    except yaml.YAMLError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_episode_yaml_content(yaml_content: str | None) -> dict | None:
    if not yaml_content:
        return None
    return parse_yaml_payload(yaml_content)


def dump_episode_yaml(payload: dict) -> str:
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)


def build_source_guard_text(
    book_title: str,
    events: list[ScriptPlotEvent],
    characters: list[ScriptCharacterDetail] | list[dict],
    chapters: list[Chapter],
) -> str:
    parts: list[str] = [book_title]
    parts.extend(event.content for event in events)
    for character in characters:
        if isinstance(character, dict):
            parts.append(str(character.get("name") or ""))
            parts.append(str(character.get("profile") or ""))
        else:
            parts.append(character.name)
            parts.append(character.profile)
    for chapter in chapters:
        parts.append(chapter.title)
        parts.append(chapter.content)
    return "\n".join(part for part in parts if part)


def episode_payload_matches_source(
    payload: dict,
    *,
    book_title: str,
    source_text: str,
) -> bool:
    script = payload.get("script") or {}
    metadata = script.get("metadata") or {}
    source_book_title = metadata.get("source_book_title")
    if source_book_title and str(source_book_title).strip() != book_title:
        return False
    rendered = dump_episode_yaml(payload)
    for marker in OFF_TOPIC_MARKERS:
        if marker in rendered and marker not in source_text:
            return False
    return True


def fallback_episode_payload(
    project: ScriptProject,
    episode_index: int,
    events: list[ScriptPlotEvent],
    book_title: str,
) -> dict:
    return {
        "script": {
            "metadata": {
                "title": f"第 {episode_index} 集",
            },
            "scenes": [
                {
                    "scene_id": index,
                    "scene_title": f"剧情事件 {event.event_index}",
                    "source_events": [event.event_index],
                    "location": "",
                    "time": "",
                    "characters": [],
                    "action": [event.content],
                    "dialogue": [],
                    "transition": "",
                }
                for index, event in enumerate(events, start=1)
            ],
        }
    }


def get_episode_format(project: ScriptProject) -> str:
    metadata = (project.yaml_schema_delta or {}).get("metadata") or {}
    value = metadata.get("format")
    if value:
        return str(value)
    return str(get_yaml_schema_delta(project.script_type or "short_drama")["metadata"]["format"])


def clean_episode_title(raw_title: Any, book_title: str, episode_number: int) -> str:
    title = str(raw_title or "").strip()
    if not title:
        return ""
    title = title.replace("《", "").replace("》", "").strip()
    if book_title:
        title = re.sub(re.escape(book_title), "", title, flags=re.IGNORECASE).strip()
    title = re.sub(r"(?i)\bepisode\s*\d+\b", "", title).strip()
    title = re.sub(rf"第\s*{episode_number}\s*[集话話回章部]?", "", title).strip()
    title = re.sub(r"第\s*[一二三四五六七八九十百千万零〇\d]+\s*[集话話回章部]", "", title).strip()
    title = re.sub(r"^[\s:：\-—_·.,，。]+", "", title).strip()
    title = re.sub(r"[\s:：\-—_]+$", "", title).strip()
    return title


def fallback_episode_title(
    payload: dict,
    events: list[ScriptPlotEvent],
    book_title: str,
    episode_number: int,
) -> str:
    script = payload.get("script") if isinstance(payload.get("script"), dict) else {}
    scenes = script.get("scenes") if isinstance(script, dict) else []
    if isinstance(scenes, list):
        for scene in scenes:
            if not isinstance(scene, dict):
                continue
            title = clean_episode_title(scene.get("scene_title"), book_title, episode_number)
            if title:
                return title
    if events:
        content = re.sub(r"\s+", "", events[0].content)
        return content[:18] or f"剧集{episode_number}"
    return f"剧集{episode_number}"


def normalize_episode_metadata(
    payload: dict,
    project: ScriptProject,
    *,
    episode_number: int,
    book_title: str,
    events: list[ScriptPlotEvent],
) -> dict:
    script = payload.setdefault("script", {})
    if not isinstance(script, dict):
        script = {}
        payload["script"] = script
    raw_metadata = script.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    title = clean_episode_title(metadata.get("title"), book_title, episode_number)
    if not title:
        title = fallback_episode_title(payload, events, book_title, episode_number)
    script["metadata"] = {
        "format": get_episode_format(project),
        "title": title,
        "episode_number": episode_number,
        "source_book_title": book_title,
        "adaptation_type": project.script_type,
        "episode_duration": project.default_target_duration,
        "pacing": project.pacing,
        "scene_frequency": project.scene_frequency,
        "dialogue_density": project.dialogue_density,
    }
    return payload


def normalize_episode_source_events(payload: dict, events: list[ScriptPlotEvent]) -> dict:
    id_to_global = {event.id: event.event_index for event in events}
    local_to_global = {index: event.event_index for index, event in enumerate(events, start=1)}
    valid_global = {event.event_index for event in events}
    valid_local = set(range(1, len(events) + 1))
    script = payload.get("script")
    if not isinstance(script, dict):
        return payload
    scenes = script.get("scenes")
    if not isinstance(scenes, list):
        return payload
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        raw_values = scene.get("source_events")
        if not isinstance(raw_values, list):
            raw_values = []
        normalized: list[int] = []
        for value in raw_values:
            try:
                number = int(value)
            except (TypeError, ValueError):
                continue
            global_index = id_to_global.get(number)
            if global_index is None and number in valid_global:
                global_index = number
            if global_index is None and number in valid_local:
                global_index = local_to_global[number]
            if global_index is not None and global_index not in normalized:
                normalized.append(global_index)
        scene["source_events"] = normalized
    return payload


def build_episode_text(payload: dict) -> str:
    script = payload.get("script") or {}
    metadata = script.get("metadata") or {}
    scenes = script.get("scenes") or []
    title = metadata.get("title") or "剧本"
    lines = [f"《{title}》"]
    if metadata.get("source_book_title"):
        lines.append(f"来源小说：{metadata.get('source_book_title')}")
    episode_number = metadata.get("episode_number") or metadata.get("episode_index")
    if episode_number:
        lines.append(f"集数：第 {episode_number} 集")
    episode_duration = metadata.get("episode_duration") or metadata.get("target_duration")
    if episode_duration:
        lines.append(f"目标时长：{episode_duration} 分钟")
    for index, scene in enumerate(scenes, start=1):
        if isinstance(scene, dict):
            scene_id = scene.get("scene_id") or index
            scene_title = scene.get("scene_title") or f"场景 {index}"
            lines.extend(["", f"场景 {scene_id}：{scene_title}"])
            if scene.get("location"):
                lines.append(f"地点：{scene.get('location')}")
            if scene.get("time"):
                lines.append(f"时间：{scene.get('time')}")
            characters = scene.get("characters") or []
            if isinstance(characters, list) and characters:
                lines.append(f"人物：{'、'.join(str(item) for item in characters)}")
            actions = (
                scene.get("action")
                or scene.get("actions")
                or scene.get("action_lines")
                or scene.get("description")
                or scene.get("summary")
                or []
            )
            if isinstance(actions, str):
                actions = [actions]
            if actions:
                lines.append("动作：")
                for action in actions:
                    lines.append(f"  {action}")
            dialogues = scene.get("dialogue") or scene.get("dialogues") or scene.get("lines") or []
            if dialogues:
                lines.append("对白：")
            for dialogue in dialogues:
                if isinstance(dialogue, dict):
                    speaker = dialogue.get("speaker") or dialogue.get("character") or ""
                    line = dialogue.get("line") or dialogue.get("content") or dialogue.get("text") or ""
                    lines.append(f"  {speaker}：{line}" if speaker else f"  {line}")
                elif dialogue:
                    lines.append(f"  {dialogue}")
            if scene.get("transition"):
                lines.append(f"转场：{scene.get('transition')}")
    return "\n".join(line for line in lines if line).strip()


def build_episode_text_from_yaml(yaml_content: str | None) -> str:
    payload = parse_episode_yaml_content(yaml_content)
    if payload is None:
        return yaml_content or ""
    return build_episode_text(payload)


def generate_one_episode(
    db: Session,
    project_id: int,
    payload: ScriptEpisodeGeneratePayload | None = None,
    *,
    clear_stop_on_finish: bool = True,
) -> ScriptEpisodeDetail | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, book_title = row
    events_per_episode = payload.events_per_episode if payload and payload.events_per_episode else project.events_per_episode
    events = get_available_events(db, project.id, events_per_episode)
    if len(events) < events_per_episode:
        raise ValueError("未锁定剧情事件不足一集额度，暂不生成新剧集")

    next_index = (
        db.scalar(
            select(func.max(ScriptEpisode.episode_index)).where(
                ScriptEpisode.project_id == project.id
            )
        )
        or 0
    ) + 1
    project.generation_status = "running"
    db.commit()

    if project.generation_stop_requested:
        project.generation_status = "stopped"
        if clear_stop_on_finish:
            project.generation_stop_requested = False
        db.commit()
        raise ValueError("已请求停止生成")

    variables = build_episode_variables(db, project, book_title, events, next_index)
    source_text = build_source_guard_text(
        book_title,
        events,
        variables["characters"],
        get_event_source_chapters(db, project, events),
    )

    # ── Phase 1: generate ────────────────────────────────────────────
    generated_yaml = None
    parsed = None
    try:
        generated_yaml = call_llm_for_task(
            db,
            task_type="script_episode_generation",
            variables=variables,
        )
        parsed = parse_yaml_payload(generated_yaml)
    except LlmServiceError:
        parsed = None
    db.refresh(project)
    if parsed and not episode_payload_matches_source(
        parsed,
        book_title=book_title,
        source_text=source_text,
    ):
        parsed = None

    # ── Phase 2: normalise + validate ────────────────────────────────
    needs_repair = False
    if parsed:
        script_payload = normalize_episode_metadata(
            parsed,
            project,
            episode_number=next_index,
            book_title=book_title,
            events=events,
        )
        script_payload = normalize_episode_source_events(script_payload, events)
    else:
        needs_repair = True  # parse failure → attempt repair below
        script_payload = None

    if script_payload is not None:
        validation_issues = validate_episode_payload(
            script_payload,
            events=events,
            episode_number=next_index,
            book_title=book_title,
        )
        if validation_issues:
            needs_repair = True
    else:
        validation_issues = []

    # ── Phase 3: repair (once) ───────────────────────────────────────
    used_fallback = False
    used_repair = False
    if needs_repair:
        repair_vars = build_episode_variables(db, project, book_title, events, next_index)
        repair_vars["validation_errors"] = [
            {"code": issue.code, "message": issue.message, "path": issue.path}
            for issue in validation_issues
        ]
        repair_vars["raw_output"] = generated_yaml or ""
        # Use yaml_schema key name expected by the repair template
        repair_vars["yaml_schema"] = repair_vars.pop("yaml_schema_delta", None)
        try:
            repair_yaml = call_llm_for_task(
                db,
                task_type="script_episode_repair",
                variables=repair_vars,
            )
            repair_parsed = parse_yaml_payload(repair_yaml)
            if repair_parsed and episode_payload_matches_source(
                repair_parsed,
                book_title=book_title,
                source_text=source_text,
            ):
                script_payload = normalize_episode_metadata(
                    repair_parsed,
                    project,
                    episode_number=next_index,
                    book_title=book_title,
                    events=events,
                )
                script_payload = normalize_episode_source_events(script_payload, events)
                # Re-validate after repair
                validation_issues = validate_episode_payload(
                    script_payload,
                    events=events,
                    episode_number=next_index,
                    book_title=book_title,
                )
                if not validation_issues:
                    used_repair = True
        except LlmServiceError:
            pass

    # ── Phase 4: fallback if still broken ────────────────────────────
    if validation_issues or script_payload is None:
        script_payload = fallback_episode_payload(project, next_index, events, book_title)
        script_payload = normalize_episode_metadata(
            script_payload, project,
            episode_number=next_index, book_title=book_title, events=events,
        )
        script_payload = normalize_episode_source_events(script_payload, events)
        validation_issues = []
        used_fallback = True

    # ── Phase 5: save ────────────────────────────────────────────────
    yaml_content = dump_episode_yaml(script_payload)
    plain_text = build_episode_text(script_payload)
    metadata = script_payload["script"]["metadata"]

    if used_fallback:
        status = "fallback"
    elif validation_issues:
        status = "draft"
    else:
        status = "completed"

    episode = ScriptEpisode(
        project_id=project.id,
        episode_index=next_index,
        title=str(metadata.get("title") or f"第 {next_index} 集"),
        event_ids=[event.id for event in events],
        yaml_content=yaml_content,
        plain_text_content=plain_text,
        status=status,
    )
    db.add(episode)
    for event in events:
        event.locked = True
    project.generation_status = (
        "stopped" if project.generation_stop_requested else "idle"
    )
    if project.generation_stop_requested and clear_stop_on_finish:
        project.generation_stop_requested = False
    db.commit()
    db.refresh(episode)
    return serialize_episode(episode)


def run_generate_all_episodes(
    project_id: int, payload: ScriptEpisodeGeneratePayload | None = None
) -> None:
    db = SessionLocal()
    try:
        row = get_project_with_book(db, project_id)
        if row is None:
            return
        project, _ = row
        while True:
            db.refresh(project)
            if project.generation_stop_requested:
                project.generation_status = "stopped"
                project.generation_stop_requested = False
                db.commit()
                break
            events_per_episode = (
                payload.events_per_episode
                if payload and payload.events_per_episode
                else project.events_per_episode
            )
            if len(get_available_events(db, project.id, events_per_episode)) < events_per_episode:
                project.generation_status = "completed"
                db.commit()
                break
            generate_one_episode(db, project_id, payload, clear_stop_on_finish=False)
    finally:
        db.close()


def start_generate_all_episodes(
    db: Session, project_id: int, payload: ScriptEpisodeGeneratePayload | None = None
) -> ScriptWorkflowProgress | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, _ = row
    project.generation_stop_requested = False
    project.generation_status = "running"
    db.commit()
    threading.Thread(
        target=run_generate_all_episodes,
        args=(project_id, payload),
        daemon=True,
    ).start()
    return get_progress(db, project_id)


def stop_episode_generation(db: Session, project_id: int) -> ScriptWorkflowProgress | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, _ = row
    project.generation_stop_requested = True
    db.commit()
    return get_progress(db, project_id)


def get_episodes(db: Session, project_id: int) -> list[ScriptEpisodeDetail] | None:
    if get_project_with_book(db, project_id) is None:
        return None
    episodes = db.scalars(
        select(ScriptEpisode)
        .where(ScriptEpisode.project_id == project_id, ScriptEpisode.is_deleted.is_(False))
        .order_by(ScriptEpisode.episode_index)
    ).all()
    return [serialize_episode(episode) for episode in episodes]


def update_episode(
    db: Session, episode_id: int, payload: ScriptEpisodeUpdate
) -> ScriptEpisodeDetail | None:
    row = db.execute(
        select(ScriptEpisode, ScriptProject, Book.title)
        .join(ScriptProject, ScriptProject.id == ScriptEpisode.project_id)
        .join(Book, Book.id == ScriptProject.book_id)
        .where(ScriptEpisode.id == episode_id, ScriptEpisode.is_deleted.is_(False))
    )
    row = row.first()
    if row is None:
        return None
    episode, project, book_title = row
    data = payload.model_dump(exclude_unset=True)
    if "title" in data and data["title"] is not None:
        episode.title = data["title"].strip()
    if "yaml_payload" in data and data["yaml_payload"] is not None:
        normalized_payload = normalize_episode_metadata(
            data["yaml_payload"],
            project,
            episode_number=episode.episode_index,
            book_title=book_title,
            events=[],
        )
        episode.yaml_content = dump_episode_yaml(normalized_payload)
    if "yaml_content" in data:
        parsed = parse_episode_yaml_content(data["yaml_content"])
        if parsed is not None:
            parsed = normalize_episode_metadata(
                parsed,
                project,
                episode_number=episode.episode_index,
                book_title=book_title,
                events=[],
            )
            episode.yaml_content = dump_episode_yaml(parsed)
        else:
            episode.yaml_content = data["yaml_content"]
    episode.plain_text_content = build_episode_text_from_yaml(episode.yaml_content)
    episode.status = "draft"
    db.commit()
    db.refresh(episode)
    return serialize_episode(episode)


def get_progress(db: Session, project_id: int) -> ScriptWorkflowProgress | None:
    row = get_project_with_book(db, project_id)
    if row is None:
        return None
    project, _ = row
    chapter_count = len(list_project_chapters(db, project))
    batches = get_batches(db, project_id) or []
    split_chapter_count = sum(
        batch.chapter_end_index - batch.chapter_start_index + 1 for batch in batches
    )
    event_count = db.scalar(
        select(func.count())
        .select_from(ScriptPlotEvent)
        .where(ScriptPlotEvent.project_id == project_id, ScriptPlotEvent.is_deleted.is_(False))
    ) or 0
    locked_event_count = db.scalar(
        select(func.count())
        .select_from(ScriptPlotEvent)
        .where(
            ScriptPlotEvent.project_id == project_id,
            ScriptPlotEvent.is_deleted.is_(False),
            ScriptPlotEvent.locked.is_(True),
        )
    ) or 0
    episode_count = db.scalar(
        select(func.count())
        .select_from(ScriptEpisode)
        .where(ScriptEpisode.project_id == project_id, ScriptEpisode.is_deleted.is_(False))
    ) or 0
    return ScriptWorkflowProgress(
        project_id=project_id,
        chapter_count=chapter_count,
        split_chapter_count=min(split_chapter_count, chapter_count),
        batch_count=len(batches),
        event_count=event_count,
        locked_event_count=locked_event_count,
        episode_count=episode_count,
        split_status=project.split_status,
        split_stop_requested=project.split_stop_requested,
        generation_status=project.generation_status,
        generation_stop_requested=project.generation_stop_requested,
    )


@dataclass(frozen=True)
class ExportFile:
    filename: str
    content: str
    media_type: str


def export_episode(db: Session, episode_id: int, file_format: str) -> ExportFile | None:
    episode = db.scalar(
        select(ScriptEpisode).where(
            ScriptEpisode.id == episode_id, ScriptEpisode.is_deleted.is_(False)
        )
    )
    if episode is None:
        return None
    normalized = file_format.lower()
    if normalized not in {"yaml", "txt"}:
        raise ValueError("only yaml and txt export are supported")
    content = (
        episode.yaml_content
        if normalized == "yaml"
        else build_episode_text_from_yaml(episode.yaml_content)
    )
    db.add(
        ExportRecord(
            project_id=episode.project_id,
            export_type="episode",
            file_format=normalized,
            file_path=f"script_episode_{episode.id}.{normalized}",
        )
    )
    db.commit()
    return ExportFile(
        filename=f"script_episode_{episode.id}.{normalized}",
        content=content or "",
        media_type="application/x-yaml; charset=utf-8"
        if normalized == "yaml"
        else "text/plain; charset=utf-8",
    )


def export_all_episodes(db: Session, project_id: int, file_format: str) -> ExportFile | None:
    if get_project_with_book(db, project_id) is None:
        return None
    normalized = file_format.lower()
    if normalized not in {"yaml", "txt"}:
        raise ValueError("only yaml and txt export are supported")
    episodes = db.scalars(
        select(ScriptEpisode)
        .where(ScriptEpisode.project_id == project_id, ScriptEpisode.is_deleted.is_(False))
        .order_by(ScriptEpisode.episode_index)
    ).all()
    if normalized == "yaml":
        content = "\n---\n".join(episode.yaml_content or "" for episode in episodes)
    else:
        content = "\n\n".join(
            build_episode_text_from_yaml(episode.yaml_content) for episode in episodes
        )
    db.add(
        ExportRecord(
            project_id=project_id,
            export_type="episode_project",
            file_format=normalized,
            file_path=f"script_project_{project_id}_episodes.{normalized}",
        )
    )
    db.commit()
    return ExportFile(
        filename=f"script_project_{project_id}_episodes.{normalized}",
        content=content,
        media_type="application/x-yaml; charset=utf-8"
        if normalized == "yaml"
        else "text/plain; charset=utf-8",
    )
