from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.book import Book
from app.models.script_project import ScriptProject
from app.models.script_segment import ScriptSegment
from app.schemas.script_project_schema import (
    ScriptProjectDetail,
    ScriptProjectListItem,
    ScriptProjectListResult,
    ScriptProjectNameUpdate,
    ScriptSegmentContentUpdate,
    ScriptSegmentDetail,
    ScriptSegmentListItem,
    ScriptSegmentNameUpdate,
)


def serialize_project(project: ScriptProject) -> ScriptProjectDetail:
    return ScriptProjectDetail(
        project_id=project.id,
        book_id=project.book_id,
        project_name=project.project_name,
        script_type=project.script_type,
        default_style=project.default_style,
        default_compression_level=project.default_compression_level,
        default_target_duration=project.default_target_duration,
        status=project.status,
    )


def serialize_segment(segment: ScriptSegment) -> ScriptSegmentDetail:
    return ScriptSegmentDetail(
        segment_id=segment.id,
        project_id=segment.project_id,
        book_id=segment.book_id,
        segment_name=segment.segment_name,
        adapt_scope=segment.adapt_scope,
        style=segment.style,
        compression_level=segment.compression_level,
        target_duration=segment.target_duration,
        scene_count=segment.scene_count,
        yaml_content=segment.yaml_content,
        plain_text_content=segment.plain_text_content,
        status=segment.status,
    )


def list_script_projects(
    db: Session,
    *,
    keyword: str | None = None,
    script_type: str | None = None,
    page: int = 1,
    size: int = 20,
) -> ScriptProjectListResult:
    count_subquery = (
        select(
            ScriptSegment.project_id,
            func.count(ScriptSegment.id).label("segment_count"),
        )
        .where(ScriptSegment.is_deleted.is_(False))
        .group_by(ScriptSegment.project_id)
        .subquery()
    )

    stmt = (
        select(
            ScriptProject,
            Book.title.label("book_title"),
            func.coalesce(count_subquery.c.segment_count, 0).label("segment_count"),
        )
        .join(Book, ScriptProject.book_id == Book.id)
        .outerjoin(count_subquery, count_subquery.c.project_id == ScriptProject.id)
        .where(ScriptProject.is_deleted.is_(False))
    )
    count_stmt = select(func.count()).select_from(ScriptProject).where(
        ScriptProject.is_deleted.is_(False)
    )

    if keyword:
        keyword_like = f"%{keyword.strip()}%"
        stmt = stmt.where(ScriptProject.project_name.ilike(keyword_like))
        count_stmt = count_stmt.where(ScriptProject.project_name.ilike(keyword_like))
    if script_type:
        stmt = stmt.where(ScriptProject.script_type == script_type)
        count_stmt = count_stmt.where(ScriptProject.script_type == script_type)

    page = max(page, 1)
    size = min(max(size, 1), 100)
    rows = db.execute(
        stmt.order_by(ScriptProject.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    total = db.scalar(count_stmt) or 0
    return ScriptProjectListResult(
        records=[
            ScriptProjectListItem(
                project_id=project.id,
                project_name=project.project_name,
                book_title=book_title,
                script_type=project.script_type,
                default_style=project.default_style,
                segment_count=segment_count,
            )
            for project, book_title, segment_count in rows
        ],
        total=total,
    )


def get_script_project(db: Session, project_id: int) -> ScriptProjectDetail | None:
    project = db.scalar(
        select(ScriptProject).where(
            ScriptProject.id == project_id, ScriptProject.is_deleted.is_(False)
        )
    )
    return serialize_project(project) if project else None


def rename_script_project(
    db: Session, project_id: int, payload: ScriptProjectNameUpdate
) -> ScriptProjectDetail | None:
    project = db.scalar(
        select(ScriptProject).where(
            ScriptProject.id == project_id, ScriptProject.is_deleted.is_(False)
        )
    )
    if project is None:
        return None
    project.project_name = payload.project_name.strip()
    db.commit()
    db.refresh(project)
    return serialize_project(project)


def delete_script_project(db: Session, project_id: int) -> bool | None:
    project = db.scalar(
        select(ScriptProject).where(
            ScriptProject.id == project_id, ScriptProject.is_deleted.is_(False)
        )
    )
    if project is None:
        return None
    project.is_deleted = True
    project.deleted_at = datetime.utcnow()
    db.commit()
    return True


def list_script_segments(db: Session, project_id: int) -> list[ScriptSegmentListItem] | None:
    project_exists = db.scalar(
        select(ScriptProject.id).where(
            ScriptProject.id == project_id, ScriptProject.is_deleted.is_(False)
        )
    )
    if project_exists is None:
        return None
    segments = db.scalars(
        select(ScriptSegment)
        .where(
            ScriptSegment.project_id == project_id,
            ScriptSegment.is_deleted.is_(False),
        )
        .order_by(ScriptSegment.created_at, ScriptSegment.id)
    ).all()
    return [
        ScriptSegmentListItem(
            segment_id=segment.id,
            segment_name=segment.segment_name,
            style=segment.style,
            compression_level=segment.compression_level,
            target_duration=segment.target_duration,
            scene_count=segment.scene_count,
            status=segment.status,
        )
        for segment in segments
    ]


def get_script_segment(db: Session, segment_id: int) -> ScriptSegmentDetail | None:
    segment = db.scalar(
        select(ScriptSegment).where(
            ScriptSegment.id == segment_id, ScriptSegment.is_deleted.is_(False)
        )
    )
    return serialize_segment(segment) if segment else None


def rename_script_segment(
    db: Session, segment_id: int, payload: ScriptSegmentNameUpdate
) -> ScriptSegmentDetail | None:
    segment = db.scalar(
        select(ScriptSegment).where(
            ScriptSegment.id == segment_id, ScriptSegment.is_deleted.is_(False)
        )
    )
    if segment is None:
        return None
    segment.segment_name = payload.segment_name.strip()
    db.commit()
    db.refresh(segment)
    return serialize_segment(segment)


def update_script_segment_content(
    db: Session, segment_id: int, payload: ScriptSegmentContentUpdate
) -> ScriptSegmentDetail | None:
    segment = db.scalar(
        select(ScriptSegment).where(
            ScriptSegment.id == segment_id, ScriptSegment.is_deleted.is_(False)
        )
    )
    if segment is None:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    if "yaml_content" in update_data:
        segment.yaml_content = update_data["yaml_content"]
    if "plain_text_content" in update_data:
        segment.plain_text_content = update_data["plain_text_content"]
    segment.status = "draft"
    db.commit()
    db.refresh(segment)
    return serialize_segment(segment)


def delete_script_segment(db: Session, segment_id: int) -> bool | None:
    segment = db.scalar(
        select(ScriptSegment).where(
            ScriptSegment.id == segment_id, ScriptSegment.is_deleted.is_(False)
        )
    )
    if segment is None:
        return None
    segment.is_deleted = True
    segment.deleted_at = datetime.utcnow()
    db.commit()
    return True
