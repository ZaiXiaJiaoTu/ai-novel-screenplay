from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.llm_call_log import LlmCallLog
from app.schemas.llm_log_schema import (
    LlmCallLogDetail,
    LlmCallLogListItem,
    LlmCallLogListResult,
)


def serialize_log_item(log: LlmCallLog) -> LlmCallLogListItem:
    return LlmCallLogListItem(
        log_id=log.id,
        llm_config_id=log.llm_config_id,
        prompt_template_id=log.prompt_template_id,
        task_type=log.task_type,
        status=log.status,
        input_tokens=log.input_tokens,
        output_tokens=log.output_tokens,
        total_tokens=log.total_tokens,
        latency_ms=log.latency_ms,
        created_at=log.created_at,
    )


def serialize_log_detail(log: LlmCallLog) -> LlmCallLogDetail:
    item = serialize_log_item(log).model_dump()
    return LlmCallLogDetail(
        **item,
        request_summary=log.request_summary,
        response_summary=log.response_summary,
        error_message=log.error_message,
    )


def list_llm_call_logs(
    db: Session,
    *,
    task_type: str | None = None,
    status: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    page: int = 1,
    size: int = 20,
) -> LlmCallLogListResult:
    stmt = select(LlmCallLog)
    count_stmt = select(func.count()).select_from(LlmCallLog)

    if task_type:
        stmt = stmt.where(LlmCallLog.task_type == task_type)
        count_stmt = count_stmt.where(LlmCallLog.task_type == task_type)
    if status:
        stmt = stmt.where(LlmCallLog.status == status)
        count_stmt = count_stmt.where(LlmCallLog.status == status)
    if start_time:
        stmt = stmt.where(LlmCallLog.created_at >= start_time)
        count_stmt = count_stmt.where(LlmCallLog.created_at >= start_time)
    if end_time:
        stmt = stmt.where(LlmCallLog.created_at <= end_time)
        count_stmt = count_stmt.where(LlmCallLog.created_at <= end_time)

    page = max(page, 1)
    size = min(max(size, 1), 100)
    logs = db.scalars(
        stmt.order_by(LlmCallLog.created_at.desc(), LlmCallLog.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    total = db.scalar(count_stmt) or 0
    return LlmCallLogListResult(
        records=[serialize_log_item(log) for log in logs],
        total=total,
    )


def get_llm_call_log(db: Session, log_id: int) -> LlmCallLogDetail | None:
    log = db.scalar(select(LlmCallLog).where(LlmCallLog.id == log_id))
    return serialize_log_detail(log) if log else None
