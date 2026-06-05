from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ScriptSegment(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "script_segments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False, index=True
    )
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("books.id"), nullable=False)
    segment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    adapt_scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    style_source: Mapped[str] = mapped_column(
        String(50), default="inherit_project", nullable=False
    )
    style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    compression_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scene_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    yaml_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    plain_text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)

    project = relationship("ScriptProject", back_populates="segments")
