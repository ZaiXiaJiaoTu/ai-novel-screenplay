from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class LlmConfig(TimestampMixin, Base):
    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_key_masked: Mapped[str] = mapped_column(String(100), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    top_p: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    max_tokens: Mapped[int | None] = mapped_column(nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(default=60, nullable=False)
    retry_count: Mapped[int] = mapped_column(default=2, nullable=False)
    task_scope: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
