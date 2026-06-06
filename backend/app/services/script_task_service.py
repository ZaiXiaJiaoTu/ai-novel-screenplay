from datetime import datetime

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.chapter import Chapter
from app.models.generation_task import GenerationArtifact, GenerationTask
from app.models.script_project import ScriptProject
from app.models.script_segment import ScriptSegment
from app.schemas.script_task_schema import (
    GenerationArtifactDetail,
    GenerationArtifactListItem,
    GenerationArtifactUpdate,
    ScriptTaskCreate,
    ScriptTaskCreateResult,
    ScriptTaskDetail,
    ScriptTaskListItem,
    ScriptTaskListResult,
)
from app.services.llm_service import LlmServiceError, call_llm_for_task
from app.utils.chapter_parser import count_words


STEP_PROGRESS = {
    None: 0,
    "style_strategy": 25,
    "scene_planning": 50,
    "script_yaml": 80,
    "save_script": 100,
}


def get_task_progress(task: GenerationTask) -> int:
    if task.status == "completed":
        return 100
    if task.status in {"pending", "canceled", "failed"}:
        return 0 if task.current_step is None else STEP_PROGRESS.get(task.current_step, 0)
    return STEP_PROGRESS.get(task.current_step, 0)


def serialize_task(task: GenerationTask) -> ScriptTaskDetail:
    return ScriptTaskDetail(
        task_id=task.id,
        status=task.status,
        current_step=task.current_step,
        progress=get_task_progress(task),
        error_message=task.error_message,
    )


def serialize_task_list_item(task: GenerationTask, book_title: str) -> ScriptTaskListItem:
    return ScriptTaskListItem(
        task_id=task.id,
        book_id=task.book_id,
        book_title=book_title,
        script_project_id=task.script_project_id,
        status=task.status,
        current_step=task.current_step,
        progress=get_task_progress(task),
        error_message=task.error_message,
        created_at=task.created_at,
        finished_at=task.finished_at,
    )


def create_script_task(db: Session, payload: ScriptTaskCreate) -> ScriptTaskCreateResult | None:
    book = db.scalar(select(Book).where(Book.id == payload.book_id, Book.is_deleted.is_(False)))
    if book is None:
        return None

    if payload.project_id is not None:
        project = db.scalar(
            select(ScriptProject).where(
                ScriptProject.id == payload.project_id,
                ScriptProject.is_deleted.is_(False),
            )
        )
        if project is None:
            raise ValueError("剧本项目不存在")
        if project.book_id != payload.book_id:
            raise ValueError("剧本项目不属于当前作品")

    task = GenerationTask(
        book_id=payload.book_id,
        script_project_id=payload.project_id,
        task_type="script_generation",
        status="pending",
        current_step=None,
        adapt_scope=payload.adapt_scope,
        generation_config=payload.generation_config,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ScriptTaskCreateResult(task_id=task.id, status=task.status)


def list_script_tasks(
    db: Session,
    *,
    book_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> ScriptTaskListResult:
    stmt = (
        select(GenerationTask, Book.title)
        .join(Book, Book.id == GenerationTask.book_id)
        .where(GenerationTask.task_type == "script_generation", Book.is_deleted.is_(False))
    )
    count_stmt = (
        select(func.count())
        .select_from(GenerationTask)
        .join(Book, Book.id == GenerationTask.book_id)
        .where(GenerationTask.task_type == "script_generation", Book.is_deleted.is_(False))
    )
    if book_id is not None:
        stmt = stmt.where(GenerationTask.book_id == book_id)
        count_stmt = count_stmt.where(GenerationTask.book_id == book_id)
    if status:
        stmt = stmt.where(GenerationTask.status == status)
        count_stmt = count_stmt.where(GenerationTask.status == status)

    page = max(page, 1)
    size = min(max(size, 1), 100)
    rows = db.execute(
        stmt.order_by(GenerationTask.created_at.desc(), GenerationTask.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    total = db.scalar(count_stmt) or 0
    return ScriptTaskListResult(
        records=[serialize_task_list_item(task, book_title) for task, book_title in rows],
        total=total,
    )


def build_placeholder_generation(book: Book, chapters: list[Chapter], task: GenerationTask) -> dict:
    generation_config = task.generation_config or {}
    adapt_scope = task.adapt_scope or {}
    script_title = f"{book.title}剧本片段"
    scene_title = chapters[0].title if chapters else "开场"
    character_names = []
    yaml_payload = {
        "script": {
            "metadata": {
                "script_id": f"task_{task.id}",
                "project_id": str(task.script_project_id or ""),
                "segment_id": "",
                "source_book_id": str(book.id),
                "title": script_title,
                "segment_title": scene_title,
                "script_type": generation_config.get("script_type", "short_drama"),
                "style": generation_config.get("style", ""),
                "compression_level": generation_config.get("compression_level", "medium"),
                "target_duration": generation_config.get("target_duration", 5),
                "duration_unit": "minute",
            },
            "adapt_scope": adapt_scope,
            "generation_config": generation_config,
            "characters": character_names,
            "scenes": [
                {
                    "scene_id": 1,
                    "scene_title": scene_title,
                    "source_chapters": [chapter.chapter_index for chapter in chapters[:3]],
                    "location": "",
                    "time": "",
                    "characters": character_names,
                    "scene_goal": "占位场景，用于打通剧本生成任务流程。",
                    "conflict": "",
                    "action": ["后续 PR 将接入大模型生成正式剧本内容。"],
                    "dialogue": [],
                    "transition": "",
                }
            ],
        }
    }
    return {
        "style_strategy": {
            "style": generation_config.get("style", ""),
            "note": "占位风格策略，后续由大模型生成。",
        },
        "scene_plan": {
            "scenes": yaml_payload["script"]["scenes"],
            "note": "占位场景规划，后续由大模型生成。",
        },
        "script_yaml": {
            "yaml": yaml.safe_dump(yaml_payload, allow_unicode=True, sort_keys=False),
            "structured": yaml_payload,
        },
    }


def strip_markdown_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_script_yaml_response(response_text: str) -> dict | None:
    raw_yaml = strip_markdown_code_fence(response_text)
    try:
        parsed = yaml.safe_load(raw_yaml)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict) or "script" not in parsed:
        return None
    return {
        "yaml": yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False),
        "structured": parsed,
    }


def build_script_plain_text(script_payload: dict) -> str:
    script = script_payload.get("script") or {}
    metadata = script.get("metadata") or {}
    scenes = script.get("scenes") or []
    lines = [
        metadata.get("segment_title") or metadata.get("title") or "剧本片段",
        *[
            f"{scene.get('scene_id', '')}. {scene.get('scene_title', '')}".strip()
            for scene in scenes
            if isinstance(scene, dict)
        ],
    ]
    return "\n".join(lines).strip()


def build_llm_variables(
    book: Book,
    chapters: list[Chapter],
    task: GenerationTask,
    generated: dict | None = None,
) -> dict:
    chapter_payload = [
        {
            "chapter_index": chapter.chapter_index,
            "title": chapter.title,
            "content": chapter.content[:3000],
        }
        for chapter in chapters
    ]
    return {
        "book_title": book.title,
        "adapt_scope": task.adapt_scope or {},
        "generation_config": task.generation_config or {},
        "chapters": chapter_payload,
        "style_strategy": (generated or {}).get("style_strategy", {}),
        "scene_plan": (generated or {}).get("scene_plan", {}),
    }


def build_generation_outputs(db: Session, book: Book, chapters: list[Chapter], task: GenerationTask) -> dict:
    generated = build_placeholder_generation(book, chapters, task)
    variables = build_llm_variables(book, chapters, task)

    try:
        style_text = call_llm_for_task(
            db,
            task_type="style_strategy_generation",
            variables=variables,
            task_id=task.id,
        )
        generated["style_strategy"] = {
            "text": style_text,
            "source": "llm",
        }
    except LlmServiceError:
        generated["style_strategy"]["source"] = "placeholder"
    except Exception as exc:
        generated["style_strategy"]["source"] = "placeholder"
        generated["style_strategy"]["llm_error"] = str(exc)

    variables = build_llm_variables(book, chapters, task, generated)
    try:
        scene_plan_text = call_llm_for_task(
            db,
            task_type="scene_plan_generation",
            variables=variables,
            task_id=task.id,
        )
        generated["scene_plan"] = {
            "text": scene_plan_text,
            "source": "llm",
        }
    except LlmServiceError:
        generated["scene_plan"]["source"] = "placeholder"
    except Exception as exc:
        generated["scene_plan"]["source"] = "placeholder"
        generated["scene_plan"]["llm_error"] = str(exc)

    variables = build_llm_variables(book, chapters, task, generated)
    try:
        script_yaml_text = call_llm_for_task(
            db,
            task_type="script_yaml_generation",
            variables=variables,
            task_id=task.id,
        )
        parsed_script_yaml = parse_script_yaml_response(script_yaml_text)
        if parsed_script_yaml is None:
            generated["script_yaml"]["source"] = "placeholder"
            generated["script_yaml"]["llm_error"] = "大模型返回内容不是有效剧本 YAML"
        else:
            generated["script_yaml"] = {
                **parsed_script_yaml,
                "source": "llm",
            }
    except LlmServiceError:
        generated["script_yaml"]["source"] = "placeholder"
    except Exception as exc:
        generated["script_yaml"]["source"] = "placeholder"
        generated["script_yaml"]["llm_error"] = str(exc)

    return generated


def save_generated_script_to_shelf(
    db: Session,
    *,
    task: GenerationTask,
    book: Book,
    generated: dict,
) -> ScriptSegment:
    generation_config = task.generation_config or {}
    script_yaml = generated["script_yaml"]
    structured = script_yaml["structured"]["script"]
    metadata = structured["metadata"]
    scenes = structured.get("scenes") or []

    project = None
    if task.script_project_id is not None:
        project = db.scalar(
            select(ScriptProject).where(
                ScriptProject.id == task.script_project_id,
                ScriptProject.is_deleted.is_(False),
            )
        )

    if project is None:
        project = ScriptProject(
            book_id=book.id,
            project_name=metadata["title"],
            script_type=metadata.get("script_type"),
            default_style=metadata.get("style"),
            default_compression_level=metadata.get("compression_level"),
            default_target_duration=metadata.get("target_duration"),
            status="ongoing",
        )
        db.add(project)
        db.flush()
        task.script_project_id = project.id

    plain_text = build_script_plain_text(script_yaml["structured"])
    segment = ScriptSegment(
        project_id=project.id,
        book_id=book.id,
        segment_name=metadata.get("segment_title") or "剧本片段",
        adapt_scope=task.adapt_scope,
        style_source="inherit_project",
        style=generation_config.get("style") or project.default_style,
        compression_level=generation_config.get("compression_level"),
        target_duration=generation_config.get("target_duration"),
        actual_word_count=count_words(plain_text),
        scene_count=len(scenes),
        yaml_content=script_yaml["yaml"],
        plain_text_content=plain_text,
        status="completed",
    )
    db.add(segment)
    return segment

def start_script_task(db: Session, task_id: int) -> ScriptTaskDetail | None:
    task = db.scalar(select(GenerationTask).where(GenerationTask.id == task_id))
    if task is None:
        return None
    if task.status == "completed":
        return serialize_task(task)
    if task.status == "canceled":
        raise ValueError("已取消的任务不能启动")

    book = db.scalar(select(Book).where(Book.id == task.book_id, Book.is_deleted.is_(False)))
    if book is None:
        task.status = "failed"
        task.error_message = "作品不存在"
        db.commit()
        return serialize_task(task)

    chapters = db.scalars(
        select(Chapter)
        .where(Chapter.book_id == book.id, Chapter.is_deleted.is_(False))
        .order_by(Chapter.chapter_index)
    ).all()

    task.status = "running"
    task.error_message = None
    generated = build_generation_outputs(db, book, list(chapters), task)
    for step, artifact_type in [
        ("style_strategy", "style_strategy"),
        ("scene_planning", "scene_plan"),
        ("script_yaml", "script_yaml"),
    ]:
        task.current_step = step
        db.add(
            GenerationArtifact(
                task_id=task.id,
                artifact_type=artifact_type,
                content=generated[artifact_type],
                version=1,
                editable=True,
            )
        )

    task.current_step = "save_script"
    save_generated_script_to_shelf(db, task=task, book=book, generated=generated)
    task.status = "completed"
    task.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return serialize_task(task)


def get_script_task(db: Session, task_id: int) -> ScriptTaskDetail | None:
    task = db.scalar(select(GenerationTask).where(GenerationTask.id == task_id))
    return serialize_task(task) if task else None


def cancel_script_task(db: Session, task_id: int) -> ScriptTaskDetail | None:
    task = db.scalar(select(GenerationTask).where(GenerationTask.id == task_id))
    if task is None:
        return None
    if task.status != "completed":
        task.status = "canceled"
        task.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
    return serialize_task(task)


def retry_script_task(db: Session, task_id: int) -> ScriptTaskDetail | None:
    task = db.scalar(select(GenerationTask).where(GenerationTask.id == task_id))
    if task is None:
        return None
    if task.status == "canceled":
        raise ValueError("已取消的任务不能重试")
    task.status = "pending"
    task.error_message = None
    db.commit()
    return start_script_task(db, task_id)


def list_task_artifacts(db: Session, task_id: int) -> list[GenerationArtifactListItem] | None:
    task_exists = db.scalar(select(GenerationTask.id).where(GenerationTask.id == task_id))
    if task_exists is None:
        return None
    artifacts = db.scalars(
        select(GenerationArtifact)
        .where(GenerationArtifact.task_id == task_id)
        .order_by(GenerationArtifact.created_at, GenerationArtifact.id)
    ).all()
    return [
        GenerationArtifactListItem(
            artifact_id=artifact.id,
            artifact_type=artifact.artifact_type,
            version=artifact.version,
            editable=artifact.editable,
        )
        for artifact in artifacts
    ]


def get_artifact(db: Session, artifact_id: int) -> GenerationArtifactDetail | None:
    artifact = db.scalar(select(GenerationArtifact).where(GenerationArtifact.id == artifact_id))
    if artifact is None:
        return None
    return GenerationArtifactDetail(
        artifact_id=artifact.id,
        task_id=artifact.task_id,
        artifact_type=artifact.artifact_type,
        content=artifact.content,
        version=artifact.version,
        editable=artifact.editable,
    )


def sync_script_yaml_artifact_to_segment(db: Session, artifact: GenerationArtifact) -> None:
    if artifact.artifact_type != "script_yaml":
        return
    task = db.scalar(select(GenerationTask).where(GenerationTask.id == artifact.task_id))
    if task is None or task.script_project_id is None:
        return

    content = artifact.content or {}
    structured = content.get("structured") if isinstance(content, dict) else None
    if not isinstance(structured, dict) or "script" not in structured:
        return

    script = structured.get("script") or {}
    metadata = script.get("metadata") or {}
    scenes = script.get("scenes") or []
    if not isinstance(metadata, dict) or not isinstance(scenes, list):
        return

    segment = db.scalar(
        select(ScriptSegment)
        .where(
            ScriptSegment.project_id == task.script_project_id,
            ScriptSegment.is_deleted.is_(False),
        )
        .order_by(ScriptSegment.created_at.desc(), ScriptSegment.id.desc())
    )
    if segment is None:
        return

    yaml_content = content.get("yaml") if isinstance(content.get("yaml"), str) else None
    segment.yaml_content = yaml_content or yaml.safe_dump(
        structured, allow_unicode=True, sort_keys=False
    )
    segment.plain_text_content = build_script_plain_text(structured)
    segment.segment_name = metadata.get("segment_title") or segment.segment_name
    segment.scene_count = len(scenes)
    segment.actual_word_count = count_words(segment.plain_text_content or "")


def update_artifact(
    db: Session, artifact_id: int, payload: GenerationArtifactUpdate
) -> GenerationArtifactDetail | None:
    artifact = db.scalar(select(GenerationArtifact).where(GenerationArtifact.id == artifact_id))
    if artifact is None:
        return None
    if not artifact.editable:
        raise ValueError("该中间成果不可编辑")
    artifact.content = payload.content
    artifact.version += 1
    sync_script_yaml_artifact_to_segment(db, artifact)
    db.commit()
    db.refresh(artifact)
    return get_artifact(db, artifact.id)
