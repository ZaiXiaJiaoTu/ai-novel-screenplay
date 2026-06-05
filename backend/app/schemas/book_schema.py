from pydantic import BaseModel, Field


class BookTextCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class BookCreateResult(BaseModel):
    book_id: int
    title: str
    preprocess_status: str


class BookListItem(BaseModel):
    book_id: int
    title: str
    novel_type: str | None
    chapter_count: int
    word_count: int
    preprocess_status: str


class BookListResult(BaseModel):
    records: list[BookListItem]
    total: int


class BookDetail(BaseModel):
    book_id: int
    title: str
    novel_type: str | None
    chapter_count: int
    word_count: int
    preprocess_status: str
    story_profile_status: str


class ChapterListItem(BaseModel):
    chapter_id: int
    chapter_index: int
    title: str
    word_count: int
