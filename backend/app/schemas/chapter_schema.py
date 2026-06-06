from pydantic import BaseModel, Field


class ChapterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    chapter_index: int | None = Field(default=None, ge=1)


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)


class ChapterDetail(BaseModel):
    chapter_id: int
    book_id: int
    chapter_index: int
    title: str
    content: str
    word_count: int


class ChapterDeleteResult(BaseModel):
    chapter_id: int
    deleted: bool
