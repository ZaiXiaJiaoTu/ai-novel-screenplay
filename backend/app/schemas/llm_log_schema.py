from datetime import datetime

from pydantic import BaseModel


class LlmCallLogListItem(BaseModel):
    log_id: int
    task_id: int | None
    llm_config_id: int | None
    prompt_template_id: int | None
    task_type: str
    status: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    latency_ms: int | None
    created_at: datetime


class LlmCallLogListResult(BaseModel):
    records: list[LlmCallLogListItem]
    total: int


class LlmCallLogDetail(LlmCallLogListItem):
    request_summary: str | None
    response_summary: str | None
    error_message: str | None
