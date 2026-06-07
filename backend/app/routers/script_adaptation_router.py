from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.script_adaptation_schema import (
    ScriptAdaptationConfigUpdate,
    ScriptAdaptationCreate,
    ScriptCharacterUpdate,
    ScriptEpisodeGeneratePayload,
    ScriptEpisodeUpdate,
    ScriptPlotEventUpdate,
)
from app.services.script_adaptation_service import (
    consolidate_character_profiles,
    create_adaptation_project,
    delete_adaptation_project,
    delete_event,
    export_all_episodes,
    export_episode,
    generate_one_episode,
    get_batches,
    get_characters,
    get_episodes,
    get_events,
    get_progress,
    list_adaptation_projects,
    repair_episode,
    start_generate_all_episodes,
    start_split_all_batches,
    split_one_batch,
    stop_episode_generation,
    stop_split,
    update_adaptation_config,
    update_character,
    update_episode,
    update_event,
)

router = APIRouter(prefix="/api/script-adaptations", tags=["script-adaptations"])


def download_response(filename: str, content: str, media_type: str) -> Response:
    encoded_filename = quote(filename)
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("")
def get_projects(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return success(list_adaptation_projects(db, page=page, size=size).model_dump())


@router.post("")
def create_project(payload: ScriptAdaptationCreate, db: Session = Depends(get_db)):
    result = create_adaptation_project(db, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="book not found")
    return success(result.model_dump())


@router.put("/{project_id}/config")
def put_project_config(
    project_id: int, payload: ScriptAdaptationConfigUpdate, db: Session = Depends(get_db)
):
    result = update_adaptation_config(db, project_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    result = delete_adaptation_project(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success({"deleted": True})


@router.get("/{project_id}/progress")
def get_project_progress(project_id: int, db: Session = Depends(get_db)):
    result = get_progress(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.post("/{project_id}/split/once")
def post_split_once(project_id: int, db: Session = Depends(get_db)):
    result = split_one_batch(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.post("/{project_id}/split/all")
def post_split_all(project_id: int, db: Session = Depends(get_db)):
    result = start_split_all_batches(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.post("/{project_id}/split/stop")
def post_split_stop(project_id: int, db: Session = Depends(get_db)):
    result = stop_split(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.get("/{project_id}/batches")
def get_project_batches(project_id: int, db: Session = Depends(get_db)):
    result = get_batches(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success([item.model_dump() for item in result])


@router.get("/{project_id}/events")
def get_project_events(project_id: int, db: Session = Depends(get_db)):
    result = get_events(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success([item.model_dump() for item in result])


@router.put("/events/{event_id}")
def put_event(event_id: int, payload: ScriptPlotEventUpdate, db: Session = Depends(get_db)):
    try:
        result = update_event(db, event_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="plot event not found")
    return success(result.model_dump())


@router.delete("/events/{event_id}")
def delete_plot_event(event_id: int, db: Session = Depends(get_db)):
    try:
        result = delete_event(db, event_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="plot event not found")
    return success({"deleted": True})


@router.get("/{project_id}/characters")
def get_project_characters(project_id: int, db: Session = Depends(get_db)):
    result = get_characters(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success([item.model_dump() for item in result])


@router.put("/characters/{character_id}")
def put_character(
    character_id: int, payload: ScriptCharacterUpdate, db: Session = Depends(get_db)
):
    result = update_character(db, character_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="character not found")
    return success(result.model_dump())


@router.post("/{project_id}/episodes/once")
def post_episode_once(
    project_id: int,
    payload: ScriptEpisodeGeneratePayload | None = None,
    db: Session = Depends(get_db),
):
    try:
        result = generate_one_episode(db, project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.post("/{project_id}/episodes/all")
def post_episode_all(
    project_id: int,
    payload: ScriptEpisodeGeneratePayload | None = None,
    db: Session = Depends(get_db),
):
    result = start_generate_all_episodes(db, project_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.post("/{project_id}/characters/consolidate")
def post_character_consolidate(project_id: int, db: Session = Depends(get_db)):
    result = consolidate_character_profiles(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success([item.model_dump() for item in result])


@router.post("/{project_id}/episodes/stop")
def post_episode_stop(project_id: int, db: Session = Depends(get_db)):
    result = stop_episode_generation(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success(result.model_dump())


@router.get("/{project_id}/episodes")
def get_project_episodes(project_id: int, db: Session = Depends(get_db)):
    result = get_episodes(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return success([item.model_dump() for item in result])


@router.put("/episodes/{episode_id}")
def put_episode(
    episode_id: int, payload: ScriptEpisodeUpdate, db: Session = Depends(get_db)
):
    result = update_episode(db, episode_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return success(result.model_dump())


@router.post("/episodes/{episode_id}/repair")
def post_episode_repair(episode_id: int, db: Session = Depends(get_db)):
    try:
        result = repair_episode(db, episode_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return success(result.model_dump())


@router.get("/episodes/{episode_id}/download")
def download_episode(
    episode_id: int,
    format: str = Query(default="yaml"),
    db: Session = Depends(get_db),
):
    try:
        result = export_episode(db, episode_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="episode not found")
    return download_response(result.filename, result.content, result.media_type)


@router.get("/{project_id}/download")
def download_project_episodes(
    project_id: int,
    format: str = Query(default="yaml"),
    db: Session = Depends(get_db),
):
    try:
        result = export_all_episodes(db, project_id, format)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="script project not found")
    return download_response(result.filename, result.content, result.media_type)
