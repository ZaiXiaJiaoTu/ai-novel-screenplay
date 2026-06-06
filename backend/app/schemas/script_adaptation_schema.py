from pydantic import BaseModel, Field


ADAPTATION_TYPES = {"tv", "short_drama", "animation", "audio_drama"}
LEVELS = {"high", "medium", "low"}
PACING = {"fast", "medium", "slow"}


class ScriptAdaptationCreate(BaseModel):
    book_id: int
    project_name: str = Field(min_length=1, max_length=255)
    adaptation_type: str = Field(pattern="^(tv|short_drama|animation|audio_drama)$")
    episode_duration: int = Field(default=10, ge=1, le=240)
    pacing: str = Field(default="medium", pattern="^(fast|medium|slow)$")
    scene_frequency: str = Field(default="medium", pattern="^(high|medium|low)$")
    dialogue_density: str = Field(default="medium", pattern="^(high|medium|low)$")
    events_per_episode: int = Field(default=10, ge=1, le=100)


class ScriptAdaptationConfigUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=255)
    episode_duration: int | None = Field(default=None, ge=1, le=240)
    pacing: str | None = Field(default=None, pattern="^(fast|medium|slow)$")
    scene_frequency: str | None = Field(default=None, pattern="^(high|medium|low)$")
    dialogue_density: str | None = Field(default=None, pattern="^(high|medium|low)$")
    events_per_episode: int | None = Field(default=None, ge=1, le=100)


class ScriptAdaptationProject(BaseModel):
    project_id: int
    book_id: int
    book_title: str
    project_name: str
    adaptation_type: str
    episode_duration: int | None
    pacing: str
    scene_frequency: str
    dialogue_density: str
    events_per_episode: int
    yaml_schema_delta: dict | None
    split_status: str
    split_stop_requested: bool
    generation_status: str
    generation_stop_requested: bool
    event_count: int
    character_count: int
    episode_count: int


class ScriptAdaptationProjectList(BaseModel):
    records: list[ScriptAdaptationProject]
    total: int


class ScriptEventBatchDetail(BaseModel):
    batch_id: int
    batch_index: int
    chapter_start_index: int
    chapter_end_index: int
    status: str
    event_count: int


class ScriptPlotEventDetail(BaseModel):
    event_id: int
    batch_id: int
    event_index: int
    content: str
    source_chapter_start: int
    source_chapter_end: int
    locked: bool


class ScriptPlotEventUpdate(BaseModel):
    content: str = Field(min_length=1)


class ScriptCharacterDetail(BaseModel):
    character_id: int
    name: str
    profile: str
    metadata_json: dict | None


class ScriptCharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    profile: str | None = None
    metadata_json: dict | None = None


class ScriptEpisodeDetail(BaseModel):
    episode_id: int
    episode_index: int
    title: str
    event_ids: list[int]
    yaml_content: str | None
    plain_text_content: str | None
    status: str


class ScriptEpisodeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    yaml_content: str | None = None
    plain_text_content: str | None = None


class ScriptWorkflowProgress(BaseModel):
    project_id: int
    chapter_count: int
    split_chapter_count: int
    batch_count: int
    event_count: int
    locked_event_count: int
    episode_count: int
    split_status: str
    split_stop_requested: bool
    generation_status: str
    generation_stop_requested: bool


class ScriptEpisodeGeneratePayload(BaseModel):
    events_per_episode: int | None = Field(default=None, ge=1, le=100)


class ScriptExportResult(BaseModel):
    filename: str
    content: str
    media_type: str
