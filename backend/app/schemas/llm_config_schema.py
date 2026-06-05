from decimal import Decimal

from pydantic import BaseModel, Field


class LlmConfigBase(BaseModel):
    provider: str = Field(min_length=1, max_length=100)
    base_url: str = Field(min_length=1, max_length=500)
    model_name: str = Field(min_length=1, max_length=100)
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    top_p: Decimal | None = Field(default=None, ge=0, le=1)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: int = Field(default=60, ge=1)
    retry_count: int = Field(default=2, ge=0)
    task_scope: list[str] | None = None
    enabled: bool = True


class LlmConfigCreate(LlmConfigBase):
    api_key: str = Field(min_length=1)
    is_default: bool = False


class LlmConfigUpdate(BaseModel):
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    api_key: str | None = Field(default=None, min_length=1)
    model_name: str | None = Field(default=None, min_length=1, max_length=100)
    temperature: Decimal | None = Field(default=None, ge=0, le=2)
    top_p: Decimal | None = Field(default=None, ge=0, le=1)
    max_tokens: int | None = Field(default=None, ge=1)
    timeout_seconds: int | None = Field(default=None, ge=1)
    retry_count: int | None = Field(default=None, ge=0)
    task_scope: list[str] | None = None
    enabled: bool | None = None
    is_default: bool | None = None


class LlmConfigDetail(LlmConfigBase):
    config_id: int
    api_key_masked: str
    is_default: bool


class LlmConfigTestResult(BaseModel):
    provider: str
    model_name: str
    latency_ms: int
    status: str
