from pydantic import BaseModel, Field


class StoryProfileBase(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    genre: str | None = Field(default=None, max_length=100)
    overview: str | None = None
    world_setting: str | None = None
    main_conflict: str | None = None
    characters: list | None = None
    relationships: list | None = None
    key_events: list | None = None
    chapter_outlines: list | None = None
    clues: list | None = None
    tone: str | None = Field(default=None, max_length=100)
    locked_settings: list | dict | None = None
    confirmed: bool | None = None


class StoryProfileUpdate(StoryProfileBase):
    pass


class StoryProfileDetail(StoryProfileBase):
    profile_id: int
    book_id: int
    version: int
    confirmed: bool
