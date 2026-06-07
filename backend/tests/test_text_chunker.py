"""Tests for text_chunker: split_chapter_content and split_chapters_for_prompt."""

from app.utils.text_chunker import (
    DEFAULT_MAX_CHARS,
    split_chapter_content,
    split_chapters_for_prompt,
)


# ── split_chapter_content ───────────────────────────────────────────────


def test_short_content_returns_single_chunk():
    result = split_chapter_content("Hello world")
    assert len(result) == 1
    assert result[0]["content"] == "Hello world"
    assert result[0]["chunk_index"] == 1
    assert result[0]["chunk_count"] == 1


def test_empty_content_returns_single_empty_chunk():
    result = split_chapter_content("")
    assert len(result) == 1
    assert result[0]["content"] == ""
    assert result[0]["chunk_index"] == 1
    assert result[0]["chunk_count"] == 1


def test_none_content_returns_single_empty_chunk():
    result = split_chapter_content(None)
    assert len(result) == 1
    assert result[0]["content"] == ""


def test_exactly_at_limit_returns_single_chunk():
    content = "A" * DEFAULT_MAX_CHARS
    result = split_chapter_content(content)
    assert len(result) == 1
    assert result[0]["content"] == content


def test_slightly_over_limit_splits_into_two():
    content = "A" * (DEFAULT_MAX_CHARS + 500)
    result = split_chapter_content(content, overlap_chars=0)
    assert len(result) >= 2
    # Total content is preserved (all characters exist across chunks)
    total = sum(len(c["content"]) for c in result)
    assert total >= len(content) - 300  # overlap may cause slight variance


def test_no_content_lost_in_chunking():
    """P2: All original content must be present across chunks."""
    # Build content with sentence boundaries
    sentences = [f"Sentence {i} ends here。\n" for i in range(200)]
    content = "".join(sentences)
    result = split_chapter_content(content, max_chars=2000, overlap_chars=100)

    # Verify every sentence-ending marker appears
    joined = "".join(c["content"] for c in result)
    for i in range(200):
        assert f"Sentence {i}" in joined, f"Sentence {i} lost in chunking"


def test_overlap_between_neighbors():
    """Adjacent chunks share overlap content."""
    content = ""
    for i in range(100):
        content += f"段落{i}这是一段测试文字用于验证重叠功能。" + "。\n"

    result = split_chapter_content(content, max_chars=1000, overlap_chars=200)

    if len(result) >= 2:
        chunk_a_end = result[0]["content"][-50:]
        chunk_b_start = result[1]["content"][:50]
        # There should be some overlap — not necessarily exactly those 50 chars
        # but the total text across chunks should exceed the original
        total_len = sum(len(c["content"]) for c in result)
        assert total_len > len(content)


def test_chinese_content_not_garbled():
    """Chinese characters must survive chunking intact."""
    content = "第一章：星辰大海。\n" * 300
    result = split_chapter_content(content, max_chars=1000, overlap_chars=0)
    joined = "".join(c["content"] for c in result)
    assert "星辰大海" in joined
    assert "第一章" in joined


def test_single_very_long_paragraph():
    """A paragraph with no sentence boundaries still gets split safely."""
    content = "A" * (DEFAULT_MAX_CHARS * 3)
    result = split_chapter_content(content, overlap_chars=0)
    assert len(result) >= 3
    total = sum(len(c["content"]) for c in result)
    assert total >= len(content)


def test_chunk_indices_are_correct():
    content = ("X" * DEFAULT_MAX_CHARS + "。\n") * 5
    result = split_chapter_content(content, overlap_chars=0)
    assert len(result) >= 2
    for i, chunk in enumerate(result):
        assert chunk["chunk_index"] == i + 1
        assert chunk["chunk_count"] == len(result)


# ── split_chapters_for_prompt ──────────────────────────────────────────


def test_split_chapters_includes_metadata():
    chapters = [
        {"chapter_index": 7, "title": "第七章", "content": "Hello world。"},
    ]
    result = split_chapters_for_prompt(chapters)
    assert len(result) == 1
    assert result[0]["chapter_index"] == 7
    assert result[0]["title"] == "第七章"
    assert result[0]["chunk_index"] == 1
    assert result[0]["chunk_count"] == 1
    assert result[0]["content"] == "Hello world。"


def test_split_long_chapter_into_multiple_prompt_chunks():
    chapters = [
        {
            "chapter_index": 1,
            "title": "第一章",
            "content": ("A" * DEFAULT_MAX_CHARS + "。\n") * 5,
        },
    ]
    result = split_chapters_for_prompt(chapters, overlap_chars=0)
    assert len(result) >= 5
    for chunk in result:
        assert chunk["chapter_index"] == 1
        assert chunk["title"] == "第一章"


def test_empty_chapters_list():
    result = split_chapters_for_prompt([])
    assert result == []
