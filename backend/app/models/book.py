from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Book(TimestampMixin, Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    novel_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chapter_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preprocess_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    story_profile_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="books", foreign_keys=[user_id])
    chapters = relationship("Chapter", back_populates="book")
    chapter_summaries = relationship("ChapterSummary", back_populates="book")
    story_profile = relationship("StoryProfile", back_populates="book", uselist=False)
    script_projects = relationship("ScriptProject", back_populates="book")
