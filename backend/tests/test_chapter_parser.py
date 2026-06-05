from app.utils.chapter_parser import count_words, detect_novel_type, parse_chapters


def test_parse_chapters_by_chinese_heading():
    content = """
第1章 旧信
林川在课桌里发现一封旧信。

第二章 旧楼
他走向旧教学楼。
""".strip()

    chapters = parse_chapters(content)

    assert len(chapters) == 2
    assert chapters[0].chapter_index == 1
    assert chapters[0].title == "第1章 旧信"
    assert "旧信" in chapters[0].content
    assert chapters[1].title == "第二章 旧楼"


def test_parse_single_chapter_when_no_heading():
    chapters = parse_chapters("没有章节标题的短篇正文")

    assert len(chapters) == 1
    assert chapters[0].title == "正文"


def test_count_words_handles_chinese_and_latin_words():
    assert count_words("林川 says hello 2026") == 5


def test_detect_novel_type():
    assert detect_novel_type(10_000, 3) == "short"
    assert detect_novel_type(40_000, 3) == "middle"
    assert detect_novel_type(10_000, 60) == "long"
