from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.services.export_service import (
    check_project_export,
    export_project,
    export_segment,
)

router = APIRouter(tags=["exports"])


def file_response(filename: str, content: str, media_type: str) -> Response:
    encoded_filename = quote(filename)
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        },
    )


@router.get("/api/script-segments/{segment_id}/download")
def download_segment(
    segment_id: int,
    format: str = Query(default="yaml"),
    db: Session = Depends(get_db),
):
    try:
        result = export_segment(db, segment_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="剧本片段不存在")
    return file_response(result.filename, result.content, result.media_type)


@router.get("/api/script-projects/{project_id}/download")
def download_project(
    project_id: int,
    format: str = Query(default="txt"),
    db: Session = Depends(get_db),
):
    try:
        result = export_project(db, project_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="剧本项目不存在")
    return file_response(result.filename, result.content, result.media_type)


@router.get("/api/script-projects/{project_id}/export-check")
def export_check(project_id: int, db: Session = Depends(get_db)):
    result = check_project_export(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本项目不存在")
    return success(result.model_dump())
