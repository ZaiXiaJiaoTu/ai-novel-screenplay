from collections.abc import Callable
from time import perf_counter
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt_text
from app.models.llm_call_log import LlmCallLog
from app.models.llm_config import LlmConfig
from app.models.prompt_template import PromptTemplate


class LlmServiceError(RuntimeError):
    pass


def summarize_text(value: str, limit: int = 500) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def render_prompt(template: str, variables: dict[str, Any]) -> str:
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
    return rendered


def find_enabled_prompt_template(db: Session, task_type: str) -> PromptTemplate | None:
    return db.scalar(
        select(PromptTemplate)
        .where(
            PromptTemplate.task_type == task_type,
            PromptTemplate.enabled.is_(True),
            PromptTemplate.is_deleted.is_(False),
        )
        .order_by(PromptTemplate.updated_at.desc())
    )


def find_llm_config(db: Session, task_type: str) -> LlmConfig | None:
    configs = db.scalars(
        select(LlmConfig)
        .where(LlmConfig.enabled.is_(True), LlmConfig.is_deleted.is_(False))
        .order_by(LlmConfig.is_default.desc(), LlmConfig.created_at.desc())
    ).all()
    for config in configs:
        if not config.task_scope or task_type in config.task_scope:
            return config
    return None


def build_chat_model(config: LlmConfig) -> ChatOpenAI:
    kwargs: dict[str, Any] = {
        "api_key": decrypt_text(config.api_key_encrypted),
        "base_url": config.base_url,
        "model": config.model_name,
        "timeout": config.timeout_seconds,
        "max_retries": config.retry_count,
    }
    if config.temperature is not None:
        kwargs["temperature"] = float(config.temperature)
    if config.top_p is not None:
        kwargs["top_p"] = float(config.top_p)
    if config.max_tokens is not None:
        kwargs["max_tokens"] = config.max_tokens
    return ChatOpenAI(**kwargs)


def extract_response_text(response: Any) -> str:
    if isinstance(response, BaseMessage):
        return str(response.content)
    content = getattr(response, "content", None)
    if content is not None:
        return str(content)
    return str(response)


def call_llm_for_task(
    db: Session,
    *,
    task_type: str,
    variables: dict[str, Any],
    task_id: int | None = None,
    model_factory: Callable[[LlmConfig], Any] = build_chat_model,
) -> str:
    prompt_template = find_enabled_prompt_template(db, task_type)
    if prompt_template is None:
        raise LlmServiceError(f"未找到启用的提示词模板: {task_type}")

    llm_config = find_llm_config(db, task_type)
    if llm_config is None:
        raise LlmServiceError(f"未找到可用的大模型配置: {task_type}")

    system_prompt = render_prompt(prompt_template.system_prompt, variables)
    user_prompt = render_prompt(prompt_template.user_prompt_template, variables)
    started_at = perf_counter()
    log = LlmCallLog(
        task_id=task_id,
        llm_config_id=llm_config.id,
        prompt_template_id=prompt_template.id,
        task_type=task_type,
        request_summary=summarize_text(user_prompt),
        status="success",
    )
    db.add(log)
    try:
        model = model_factory(llm_config)
        response = model.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
        response_text = extract_response_text(response)
        log.response_summary = summarize_text(response_text)
        log.latency_ms = int((perf_counter() - started_at) * 1000)
        db.commit()
        return response_text
    except Exception as exc:
        log.status = "failed"
        log.error_message = str(exc)
        log.latency_ms = int((perf_counter() - started_at) * 1000)
        db.commit()
        raise
