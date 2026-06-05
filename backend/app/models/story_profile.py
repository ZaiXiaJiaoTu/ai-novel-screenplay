from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class StoryProfile(TimestampMixin, Base):
    __tablename__ = "story_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("books.id"), nullable=False, unique=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)
    world_setting: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_conflict: Mapped[str | None] = mapped_column(Text, nullable=True)
    characters: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    relationships: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    key_events: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    chapter_outlines: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    clues: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    locked_settings: Mapped[list | dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    book = relationship("Book", back_populates="story_profile")
