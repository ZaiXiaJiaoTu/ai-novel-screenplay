from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.export_record import ExportRecord
from app.models.script_project import ScriptProject
from app.models.script_segment import ScriptSegment
from app.schemas.export_schema import ExportCheckResult


SUPPORTED_FORMATS = {"yaml", "txt"}


@dataclass(frozen=True)
class ExportFile:
    filename: str
    content: str
    media_type: str


def validate_format(file_format: str) -> str:
    normalized = file_format.lower()
    if normalized not in SUPPORTED_FORMATS:
        raise ValueError("暂只支持 yaml 和 txt 格式")
    return normalized


def get_segment_for_export(db: Session, segment_id: int) -> ScriptSegment | None:
    return db.scalar(
        select(ScriptSegment).where(
            ScriptSegment.id == segment_id,
            ScriptSegment.is_deleted.is_(False),
        )
    )


def build_segment_export(segment: ScriptSegment, file_format: str) -> ExportFile:
    normalized = validate_format(file_format)
    if normalized == "yaml":
        content = segment.yaml_content or ""
        extension = "yaml"
        media_type = "application/x-yaml; charset=utf-8"
    else:
        content = segment.plain_text_content or segment.yaml_content or ""
        extension = "txt"
        media_type = "text/plain; charset=utf-8"

    filename = f"script_segment_{segment.id}.{extension}"
    return ExportFile(filename=filename, content=content, media_type=media_type)


def export_segment(db: Session, segment_id: int, file_format: str) -> ExportFile | None:
    segment = get_segment_for_export(db, segment_id)
    if segment is None:
        return None
    export_file = build_segment_export(segment, file_format)
    db.add(
        ExportRecord(
            project_id=segment.project_id,
            segment_id=segment.id,
            export_type="segment",
            file_format=validate_format(file_format),
            file_path=export_file.filename,
        )
    )
    db.commit()
    return export_file


def get_project_segments_for_export(db: Session, project_id: int) -> list[ScriptSegment] | None:
    project_exists = db.scalar(
        select(ScriptProject.id).where(
            ScriptProject.id == project_id,
            ScriptProject.is_deleted.is_(False),
        )
    )
    if project_exists is None:
        return None
    return list(
        db.scalars(
            select(ScriptSegment)
            .where(
                ScriptSegment.project_id == project_id,
                ScriptSegment.is_deleted.is_(False),
            )
            .order_by(ScriptSegment.created_at, ScriptSegment.id)
        ).all()
    )


def build_project_export(
    project_id: int, segments: list[ScriptSegment], file_format: str
) -> ExportFile:
    normalized = validate_format(file_format)
    if normalized == "yaml":
        content = "\n---\n".join(segment.yaml_content or "" for segment in segments)
        extension = "yaml"
        media_type = "application/x-yaml; charset=utf-8"
    else:
        content = "\n\n".join(
            segment.plain_text_content or segment.yaml_content or "" for segment in segments
        )
        extension = "txt"
        media_type = "text/plain; charset=utf-8"
    return ExportFile(
        filename=f"script_project_{project_id}.{extension}",
        content=content,
        media_type=media_type,
    )


def export_project(db: Session, project_id: int, file_format: str) -> ExportFile | None:
    segments = get_project_segments_for_export(db, project_id)
    if segments is None:
        return None
    export_file = build_project_export(project_id, segments, file_format)
    db.add(
        ExportRecord(
            project_id=project_id,
            segment_id=None,
            export_type="project",
            file_format=validate_format(file_format),
            file_path=export_file.filename,
        )
    )
    db.commit()
    return export_file


def check_project_export(db: Session, project_id: int) -> ExportCheckResult | None:
    segments = get_project_segments_for_export(db, project_id)
    if segments is None:
        return None

    warnings: list[str] = []
    if not segments:
        warnings.append("当前剧本项目没有可导出的剧本片段")

    styles = {segment.style for segment in segments if segment.style}
    durations = {
        segment.target_duration for segment in segments if segment.target_duration is not None
    }
    style_consistent = len(styles) <= 1
    duration_consistent = len(durations) <= 1
    if not style_consistent:
        warnings.append("当前剧本项目包含多个风格片段")
    if not duration_consistent:
        warnings.append("当前剧本项目包含多个目标时长")

    # 初版没有保存章节连续区间，先只检查片段顺序是否存在。
    chapter_continuous = bool(segments)
    if not chapter_continuous:
        warnings.append("无法检查章节连续性")

    return ExportCheckResult(
        chapter_continuous=chapter_continuous,
        style_consistent=style_consistent,
        duration_consistent=duration_consistent,
        warnings=warnings,
    )
