from pydantic import BaseModel, Field


class ScriptProjectListItem(BaseModel):
    project_id: int
    project_name: str
    book_title: str
    script_type: str | None
    default_style: str | None
    segment_count: int


class ScriptProjectListResult(BaseModel):
    records: list[ScriptProjectListItem]
    total: int


class ScriptProjectDetail(BaseModel):
    project_id: int
    book_id: int
    project_name: str
    script_type: str | None
    default_style: str | None
    default_compression_level: str | None
    default_target_duration: int | None
    status: str


class ScriptProjectNameUpdate(BaseModel):
    project_name: str = Field(min_length=1, max_length=255)


class ScriptSegmentListItem(BaseModel):
    segment_id: int
    segment_name: str
    style: str | None
    compression_level: str | None
    target_duration: int | None
    scene_count: int
    status: str


class ScriptSegmentDetail(ScriptSegmentListItem):
    project_id: int
    book_id: int
    adapt_scope: dict | None
    yaml_content: str | None
    plain_text_content: str | None


class ScriptSegmentNameUpdate(BaseModel):
    segment_name: str = Field(min_length=1, max_length=255)


class ScriptSegmentContentUpdate(BaseModel):
    yaml_content: str | None = None
    plain_text_content: str | None = None
