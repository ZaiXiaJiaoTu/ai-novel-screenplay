from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.services.llm_log_service import get_llm_call_log, list_llm_call_logs

router = APIRouter(prefix="/api/llm-call-logs", tags=["llm-call-logs"])


@router.get("")
def get_logs(
    task_type: str | None = None,
    status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return success(
        list_llm_call_logs(
            db,
            task_type=task_type,
            status=status,
            start_time=start_time,
            end_time=end_time,
            page=page,
            size=size,
        ).model_dump()
    )


@router.get("/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)):
    result = get_llm_call_log(db, log_id)
    if result is None:
        raise HTTPException(status_code=404, detail="调用日志不存在")
    return success(result.model_dump())
