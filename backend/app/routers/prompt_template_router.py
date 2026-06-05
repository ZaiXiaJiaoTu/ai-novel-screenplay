from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.prompt_template_schema import PromptTemplateCreate, PromptTemplateUpdate
from app.services.prompt_template_service import (
    create_prompt_template,
    delete_prompt_template,
    list_prompt_template_versions,
    list_prompt_templates,
    rollback_prompt_template,
    update_prompt_template,
)

router = APIRouter(prefix="/api/prompt-templates", tags=["prompt-templates"])


@router.post("")
def create_template(payload: PromptTemplateCreate, db: Session = Depends(get_db)):
    return success(create_prompt_template(db, payload).model_dump())


@router.get("")
def get_templates(
    task_type: str | None = None,
    enabled: bool | None = Query(default=None),
    keyword: str | None = None,
    db: Session = Depends(get_db),
):
    return success(
        [
            item.model_dump()
            for item in list_prompt_templates(
                db, task_type=task_type, enabled=enabled, keyword=keyword
            )
        ]
    )


@router.put("/{template_id}")
def put_template(
    template_id: int,
    payload: PromptTemplateUpdate,
    db: Session = Depends(get_db),
):
    result = update_prompt_template(db, template_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return success(result.model_dump())


@router.delete("/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    result = delete_prompt_template(db, template_id)
    if result is None:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return success({"deleted": True})


@router.get("/{template_id}/versions")
def get_template_versions(template_id: int, db: Session = Depends(get_db)):
    result = list_prompt_template_versions(db, template_id)
    if result is None:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return success([item.model_dump() for item in result])


@router.post("/{template_id}/rollback/{version_id}")
def rollback_template(
    template_id: int, version_id: int, db: Session = Depends(get_db)
):
    try:
        result = rollback_prompt_template(db, template_id, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="提示词模板不存在")
    return success(result.model_dump())
