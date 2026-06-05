from time import perf_counter

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import encrypt_text, mask_api_key
from app.models.llm_config import LlmConfig
from app.schemas.llm_config_schema import (
    LlmConfigCreate,
    LlmConfigDetail,
    LlmConfigTestResult,
    LlmConfigUpdate,
)


def serialize_llm_config(config: LlmConfig) -> LlmConfigDetail:
    return LlmConfigDetail(
        config_id=config.id,
        provider=config.provider,
        base_url=config.base_url,
        api_key_masked=config.api_key_masked,
        model_name=config.model_name,
        temperature=config.temperature,
        top_p=config.top_p,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
        retry_count=config.retry_count,
        task_scope=config.task_scope,
        is_default=config.is_default,
        enabled=config.enabled,
    )


def clear_default_configs(db: Session) -> None:
    db.execute(
        update(LlmConfig)
        .where(LlmConfig.is_deleted.is_(False), LlmConfig.is_default.is_(True))
        .values(is_default=False)
    )


def create_llm_config(db: Session, payload: LlmConfigCreate) -> LlmConfigDetail:
    if payload.is_default:
        clear_default_configs(db)
    config = LlmConfig(
        provider=payload.provider,
        base_url=payload.base_url,
        api_key_encrypted=encrypt_text(payload.api_key),
        api_key_masked=mask_api_key(payload.api_key),
        model_name=payload.model_name,
        temperature=payload.temperature,
        top_p=payload.top_p,
        max_tokens=payload.max_tokens,
        timeout_seconds=payload.timeout_seconds,
        retry_count=payload.retry_count,
        task_scope=payload.task_scope,
        is_default=payload.is_default,
        enabled=payload.enabled,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return serialize_llm_config(config)


def list_llm_configs(db: Session) -> list[LlmConfigDetail]:
    configs = db.scalars(
        select(LlmConfig)
        .where(LlmConfig.is_deleted.is_(False))
        .order_by(LlmConfig.is_default.desc(), LlmConfig.created_at.desc())
    ).all()
    return [serialize_llm_config(config) for config in configs]


def get_llm_config_model(db: Session, config_id: int) -> LlmConfig | None:
    return db.scalar(
        select(LlmConfig).where(
            LlmConfig.id == config_id,
            LlmConfig.is_deleted.is_(False),
        )
    )


def update_llm_config(
    db: Session, config_id: int, payload: LlmConfigUpdate
) -> LlmConfigDetail | None:
    config = get_llm_config_model(db, config_id)
    if config is None:
        return None
    update_data = payload.model_dump(exclude_unset=True)
    api_key = update_data.pop("api_key", None)
    if api_key:
        config.api_key_encrypted = encrypt_text(api_key)
        config.api_key_masked = mask_api_key(api_key)
    if update_data.get("is_default") is True:
        clear_default_configs(db)
    for field_name, value in update_data.items():
        setattr(config, field_name, value)
    db.commit()
    db.refresh(config)
    return serialize_llm_config(config)


def delete_llm_config(db: Session, config_id: int) -> bool | None:
    config = get_llm_config_model(db, config_id)
    if config is None:
        return None
    config.is_deleted = True
    config.is_default = False
    db.commit()
    return True


def set_default_llm_config(db: Session, config_id: int) -> LlmConfigDetail | None:
    config = get_llm_config_model(db, config_id)
    if config is None:
        return None
    clear_default_configs(db)
    config.is_default = True
    config.enabled = True
    db.commit()
    db.refresh(config)
    return serialize_llm_config(config)


def test_llm_config(db: Session, config_id: int) -> LlmConfigTestResult | None:
    config = get_llm_config_model(db, config_id)
    if config is None:
        return None
    start = perf_counter()
    if not config.enabled:
        raise ValueError("模型配置未启用")
    if not config.base_url.startswith(("http://", "https://")):
        raise ValueError("base_url 必须以 http:// 或 https:// 开头")
    latency_ms = int((perf_counter() - start) * 1000)
    return LlmConfigTestResult(
        provider=config.provider,
        model_name=config.model_name,
        latency_ms=latency_ms,
        status="validated",
    )
