from pydantic import BaseModel


class ExportCheckResult(BaseModel):
    chapter_continuous: bool
    style_consistent: bool
    duration_consistent: bool
    warnings: list[str]
