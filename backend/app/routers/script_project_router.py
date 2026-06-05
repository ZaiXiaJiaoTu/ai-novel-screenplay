from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.script_project_schema import (
    ScriptProjectNameUpdate,
    ScriptSegmentContentUpdate,
    ScriptSegmentNameUpdate,
)
from app.services.script_project_service import (
    delete_script_project,
    delete_script_segment,
    get_script_project,
    get_script_segment,
    list_script_projects,
    list_script_segments,
    rename_script_project,
    rename_script_segment,
    update_script_segment_content,
)

router = APIRouter(tags=["script-projects"])


@router.get("/api/script-projects")
def get_projects(
    keyword: str | None = None,
    script_type: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return success(
        list_script_projects(
            db, keyword=keyword, script_type=script_type, page=page, size=size
        ).model_dump()
    )


@router.get("/api/script-projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    result = get_script_project(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本项目不存在")
    return success(result.model_dump())


@router.put("/api/script-projects/{project_id}/name")
def put_project_name(
    project_id: int, payload: ScriptProjectNameUpdate, db: Session = Depends(get_db)
):
    result = rename_script_project(db, project_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本项目不存在")
    return success(result.model_dump())


@router.delete("/api/script-projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    result = delete_script_project(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本项目不存在")
    return success({"deleted": True})


@router.get("/api/script-projects/{project_id}/segments")
def get_segments(project_id: int, db: Session = Depends(get_db)):
    result = list_script_segments(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本项目不存在")
    return success([item.model_dump() for item in result])


@router.get("/api/script-segments/{segment_id}")
def get_segment(segment_id: int, db: Session = Depends(get_db)):
    result = get_script_segment(db, segment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本片段不存在")
    return success(result.model_dump())


@router.put("/api/script-segments/{segment_id}/name")
def put_segment_name(
    segment_id: int, payload: ScriptSegmentNameUpdate, db: Session = Depends(get_db)
):
    result = rename_script_segment(db, segment_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本片段不存在")
    return success(result.model_dump())


@router.put("/api/script-segments/{segment_id}/content")
def put_segment_content(
    segment_id: int, payload: ScriptSegmentContentUpdate, db: Session = Depends(get_db)
):
    result = update_script_segment_content(db, segment_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本片段不存在")
    return success(result.model_dump())


@router.delete("/api/script-segments/{segment_id}")
def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    result = delete_script_segment(db, segment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="剧本片段不存在")
    return success({"deleted": True})
