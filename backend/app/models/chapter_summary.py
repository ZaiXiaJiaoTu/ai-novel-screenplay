from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ChapterSummary(TimestampMixin, Base):
    __tablename__ = "chapter_summaries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("books.id"), nullable=False, index=True
    )
    chapter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("chapters.id"), nullable=False, index=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    characters: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    key_events: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    locations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    clues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    emotion_changes: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    book = relationship("Book", back_populates="chapter_summaries")
    chapter = relationship("Chapter", back_populates="summary")
