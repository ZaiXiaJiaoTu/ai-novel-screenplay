import re
from dataclasses import dataclass


CHAPTER_HEADING_PATTERN = re.compile(
    r"^\s*(第[零〇一二三四五六七八九十百千万\d]+[章节卷回部].*|Chapter\s+\d+.*)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class ParsedChapter:
    chapter_index: int
    title: str
    content: str
    word_count: int


def count_words(text: str) -> int:
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    latin_words = re.findall(r"[A-Za-z0-9]+(?:[-_'][A-Za-z0-9]+)?", text)
    return len(chinese_chars) + len(latin_words)


def detect_novel_type(word_count: int, chapter_count: int) -> str:
    if word_count > 150_000 or chapter_count > 50:
        return "long"
    if word_count > 30_000 or chapter_count > 10:
        return "middle"
    return "short"


def parse_chapters(content: str) -> list[ParsedChapter]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []

    matches = list(CHAPTER_HEADING_PATTERN.finditer(normalized))
    if not matches:
        return [
            ParsedChapter(
                chapter_index=1,
                title="正文",
                content=normalized,
                word_count=count_words(normalized),
            )
        ]

    chapters: list[ParsedChapter] = []
    preface = normalized[: matches[0].start()].strip()
    if preface:
        chapters.append(
            ParsedChapter(
                chapter_index=1,
                title="序章",
                content=preface,
                word_count=count_words(preface),
            )
        )

    for idx, match in enumerate(matches):
        next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)
        title = match.group(1).strip()
        body = normalized[match.end() : next_start].strip()
        chapter_content = body or title
        chapters.append(
            ParsedChapter(
                chapter_index=len(chapters) + 1,
                title=title,
                content=chapter_content,
                word_count=count_words(chapter_content),
            )
        )

    return chapters
