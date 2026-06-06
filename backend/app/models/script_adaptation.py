from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ScriptEventBatch(TimestampMixin, Base):
    __tablename__ = "script_event_batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False, index=True
    )
    book_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("books.id"), nullable=False)
    batch_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter_start_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chapter_end_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    events = relationship("ScriptPlotEvent", back_populates="batch")


class ScriptPlotEvent(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "script_plot_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False, index=True
    )
    batch_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_event_batches.id"), nullable=False, index=True
    )
    event_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_chapter_start: Mapped[int] = mapped_column(Integer, nullable=False)
    source_chapter_end: Mapped[int] = mapped_column(Integer, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    batch = relationship("ScriptEventBatch", back_populates="events")


class ScriptCharacterProfile(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "script_character_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class ScriptCharacterFact(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "script_character_facts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False, index=True
    )
    character_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_character_profiles.id"), nullable=False, index=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("script_event_batches.id"), nullable=True, index=True
    )
    fact_type: Mapped[str] = mapped_column(String(100), default="设定", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_content: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


class ScriptEpisode(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "script_episodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False, index=True
    )
    episode_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_ids: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    yaml_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    plain_text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
