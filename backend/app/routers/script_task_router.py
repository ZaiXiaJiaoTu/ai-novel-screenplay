from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.script_task_schema import GenerationArtifactUpdate, ScriptTaskCreate
from app.services.script_task_service import (
    cancel_script_task,
    create_script_task,
    get_artifact,
    get_script_task,
    list_task_artifacts,
    retry_script_task,
    start_script_task,
    update_artifact,
)

router = APIRouter(tags=["script-tasks"])


@router.post("/api/script-tasks")
def create_task(payload: ScriptTaskCreate, db: Session = Depends(get_db)):
    try:
        result = create_script_task(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return success(result.model_dump())


@router.post("/api/script-tasks/{task_id}/start")
def start_task(task_id: int, db: Session = Depends(get_db)):
    try:
        result = start_script_task(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success(result.model_dump())


@router.get("/api/script-tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    result = get_script_task(db, task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success(result.model_dump())


@router.post("/api/script-tasks/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    result = cancel_script_task(db, task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success(result.model_dump())


@router.post("/api/script-tasks/{task_id}/retry")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    try:
        result = retry_script_task(db, task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success(result.model_dump())


@router.get("/api/script-tasks/{task_id}/artifacts")
def get_task_artifacts(task_id: int, db: Session = Depends(get_db)):
    result = list_task_artifacts(db, task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return success([item.model_dump() for item in result])


@router.get("/api/artifacts/{artifact_id}")
def get_artifact_detail(artifact_id: int, db: Session = Depends(get_db)):
    result = get_artifact(db, artifact_id)
    if result is None:
        raise HTTPException(status_code=404, detail="中间成果不存在")
    return success(result.model_dump())


@router.put("/api/artifacts/{artifact_id}")
def put_artifact(
    artifact_id: int,
    payload: GenerationArtifactUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = update_artifact(db, artifact_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="中间成果不存在")
    return success(result.model_dump())
