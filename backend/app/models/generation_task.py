from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class GenerationTask(TimestampMixin, Base):
    __tablename__ = "generation_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    book_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("books.id"), nullable=False, index=True
    )
    script_project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=True
    )
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    adapt_scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generation_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="generation_tasks")
    artifacts = relationship("GenerationArtifact", back_populates="task")


class GenerationArtifact(TimestampMixin, Base):
    __tablename__ = "generation_artifacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("generation_tasks.id"), nullable=False, index=True
    )
    artifact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    editable: Mapped[bool] = mapped_column(default=True, nullable=False)

    task = relationship("GenerationTask", back_populates="artifacts")
