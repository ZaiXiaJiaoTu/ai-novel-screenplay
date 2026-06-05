from types import SimpleNamespace

from app.services.export_service import (
    build_project_export,
    build_segment_export,
    check_project_export,
    validate_format,
)


def test_build_segment_export_yaml_and_txt():
    segment = SimpleNamespace(
        id=1,
        yaml_content="script:\n  title: 长夜来信",
        plain_text_content="剧本文本",
    )

    yaml_file = build_segment_export(segment, "yaml")
    txt_file = build_segment_export(segment, "txt")

    assert yaml_file.filename == "script_segment_1.yaml"
    assert "script:" in yaml_file.content
    assert txt_file.filename == "script_segment_1.txt"
    assert txt_file.content == "剧本文本"


def test_build_project_export_joins_segments():
    segments = [
        SimpleNamespace(yaml_content="script: 1", plain_text_content="第一段"),
        SimpleNamespace(yaml_content="script: 2", plain_text_content="第二段"),
    ]

    result = build_project_export(10, segments, "txt")

    assert result.filename == "script_project_10.txt"
    assert result.content == "第一段\n\n第二段"


def test_validate_format_rejects_unsupported_format():
    try:
        validate_format("pdf")
    except ValueError as exc:
        assert "yaml" in str(exc)
    else:
        raise AssertionError("pdf should not be supported yet")
