from pydantic import BaseModel, Field


class ScriptTaskCreate(BaseModel):
    book_id: int
    project_id: int | None = None
    adapt_scope: dict = Field(default_factory=dict)
    generation_config: dict = Field(default_factory=dict)


class ScriptTaskCreateResult(BaseModel):
    task_id: int
    status: str


class ScriptTaskDetail(BaseModel):
    task_id: int
    status: str
    current_step: str | None
    progress: int
    error_message: str | None


class GenerationArtifactListItem(BaseModel):
    artifact_id: int
    artifact_type: str
    version: int
    editable: bool


class GenerationArtifactDetail(GenerationArtifactListItem):
    task_id: int
    content: dict | list | None


class GenerationArtifactUpdate(BaseModel):
    content: dict | list
