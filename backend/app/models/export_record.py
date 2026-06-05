from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import CreatedAtMixin


class ExportRecord(CreatedAtMixin, Base):
    __tablename__ = "export_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    project_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("script_projects.id"), nullable=False
    )
    segment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("script_segments.id"), nullable=True
    )
    export_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
