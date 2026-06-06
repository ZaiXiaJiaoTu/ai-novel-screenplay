from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import CreatedAtMixin


class LlmCallLog(CreatedAtMixin, Base):
    __tablename__ = "llm_call_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    llm_config_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("llm_configs.id"), nullable=True
    )
    prompt_template_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("prompt_templates.id"), nullable=True
    )
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    request_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
