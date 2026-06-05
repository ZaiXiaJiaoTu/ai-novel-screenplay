from pydantic import BaseModel


class ChapterDetail(BaseModel):
    chapter_id: int
    book_id: int
    chapter_index: int
    title: str
    content: str
    word_count: int


class ChapterSummaryDetail(BaseModel):
    summary_id: int
    book_id: int
    chapter_id: int
    chapter_index: int
    chapter_title: str
    summary: str | None
    characters: list
    key_events: list
    locations: list
    clues: list
    emotion_changes: list


class ChapterSummaryGenerationResult(BaseModel):
    book_id: int
    generated_count: int
    summaries: list[ChapterSummaryDetail]
