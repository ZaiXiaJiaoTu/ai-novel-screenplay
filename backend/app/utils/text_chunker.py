"""Chapter text chunking to avoid silent truncation of long content.

Replaces the fixed ``content[:5000]`` pattern used previously in
``build_split_variables`` and ``build_episode_variables``.
"""

import re

# ── constants ───────────────────────────────────────────────────────────────

DEFAULT_MAX_CHARS: int = 5000
"""Default maximum characters per chunk."""

DEFAULT_OVERLAP_CHARS: int = 300
"""Character overlap between adjacent chunks to preserve context."""

# Chinese/English sentence boundary patterns
_SENTENCE_BOUNDARY = re.compile(
    r"[。！？!?\n](?=\S)", flags=re.UNICODE
)


def split_chapter_content(
    content: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[dict]:
    """Split a chapter's text into overlapping chunks at sentence boundaries.

    Each returned chunk is a dict with::

        {
            "content": "...",
            "chunk_index": 1,
            "chunk_count": 3,
        }

    The calling code is expected to add ``chapter_index`` and ``title``.

    - Content shorter than *max_chars* is returned as a single chunk.
    - Splits are made at the nearest sentence boundary before the limit.
    - Adjacent chunks overlap by *overlap_chars* characters.
    - No content is silently discarded.
    """
    text = (content or "").strip()
    if not text:
        return [{"content": "", "chunk_index": 1, "chunk_count": 1}]

    if len(text) <= max_chars:
        return [{"content": text, "chunk_index": 1, "chunk_count": 1}]

    chunks_content: list[str] = []
    remaining = text
    effective_max = max(max_chars, overlap_chars + 100)

    while len(remaining) > max_chars:
        # Find the best split point: sentence boundary before max_chars
        segment = remaining[:effective_max]
        split_at = _find_split_point(segment, max_chars)

        chunks_content.append(remaining[:split_at].strip())

        # Advance with overlap
        overlap_start = max(0, split_at - overlap_chars)
        remaining = remaining[overlap_start:]

        # Safety: prevent infinite loop on extremely long paragraphs
        if len(chunks_content) > 1000:
            # Force-split remaining at max_chars
            chunks_content.append(remaining[:max_chars].strip())
            remaining = remaining[max_chars:]
            break

    if remaining.strip():
        chunks_content.append(remaining.strip())

    chunk_count = len(chunks_content)
    return [
        {
            "content": chunk_text,
            "chunk_index": index + 1,
            "chunk_count": chunk_count,
        }
        for index, chunk_text in enumerate(chunks_content)
    ]


def _find_split_point(segment: str, preferred_limit: int) -> int:
    """Find the best sentence boundary in *segment* near *preferred_limit*.

    Returns the character index at which to split.
    """
    # Search for sentence boundaries within the segment
    boundaries: list[int] = []
    for match in _SENTENCE_BOUNDARY.finditer(segment):
        boundaries.append(match.end())

    if not boundaries:
        # No sentence boundary found — use paragraph break or hard cut
        para_breaks = [m.end() for m in re.finditer(r"\n\s*\n", segment)]
        if para_breaks:
            # Use the last paragraph break before preferred_limit
            candidates = [p for p in para_breaks if p <= preferred_limit]
            if candidates:
                return candidates[-1]
        return preferred_limit

    # Prefer a boundary close to but not exceeding preferred_limit
    candidates = [b for b in boundaries if b <= preferred_limit]
    if candidates:
        return candidates[-1]

    # All boundaries are past the limit — use the first one
    return boundaries[0]


def split_chapters_for_prompt(
    chapters: list[dict],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[dict]:
    """Split a list of chapter dicts into prompt-ready chunks.

    Each input dict should have ``chapter_index``, ``title``, ``content``.
    Output dicts add ``chunk_index`` and ``chunk_count``.
    """
    result: list[dict] = []
    for chapter in chapters:
        chunk_index = int(chapter.get("chapter_index") or 0)
        title = str(chapter.get("title") or "")
        content = str(chapter.get("content") or "")
        for chunk in split_chapter_content(
            content,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        ):
            result.append(
                {
                    "chapter_index": chunk_index,
                    "title": title,
                    "chunk_index": chunk["chunk_index"],
                    "chunk_count": chunk["chunk_count"],
                    "content": chunk["content"],
                }
            )
    return result
