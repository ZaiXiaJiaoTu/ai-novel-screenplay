from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.schemas.llm_config_schema import LlmConfigCreate, LlmConfigUpdate
from app.services.llm_config_service import (
    create_llm_config,
    delete_llm_config,
    list_llm_configs,
    set_default_llm_config,
    test_llm_config,
    update_llm_config,
)

router = APIRouter(prefix="/api/llm-configs", tags=["llm-configs"])


@router.post("")
def create_config(payload: LlmConfigCreate, db: Session = Depends(get_db)):
    return success(create_llm_config(db, payload).model_dump())


@router.get("")
def get_configs(db: Session = Depends(get_db)):
    return success([item.model_dump() for item in list_llm_configs(db)])


@router.put("/{config_id}")
def put_config(
    config_id: int,
    payload: LlmConfigUpdate,
    db: Session = Depends(get_db),
):
    result = update_llm_config(db, config_id, payload)
    if result is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return success(result.model_dump())


@router.delete("/{config_id}")
def delete_config(config_id: int, db: Session = Depends(get_db)):
    result = delete_llm_config(db, config_id)
    if result is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return success({"deleted": True})


@router.post("/{config_id}/default")
def set_default_config(config_id: int, db: Session = Depends(get_db)):
    result = set_default_llm_config(db, config_id)
    if result is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return success(result.model_dump())


@router.post("/{config_id}/test")
def test_config(config_id: int, db: Session = Depends(get_db)):
    try:
        result = test_llm_config(db, config_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    return success(result.model_dump())
