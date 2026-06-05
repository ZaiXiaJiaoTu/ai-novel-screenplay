from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ScriptProject(SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "script_projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True, index=True
    )
    book_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("books.id"), nullable=False, index=True
    )
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    script_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    default_compression_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_target_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="ongoing", nullable=False)

    user = relationship("User", back_populates="script_projects")
    book = relationship("Book", back_populates="script_projects")
    segments = relationship("ScriptSegment", back_populates="project")
