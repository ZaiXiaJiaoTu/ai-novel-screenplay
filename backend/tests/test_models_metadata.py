from app.core.database import Base
from app import models  # noqa: F401
from sqlalchemy.orm import configure_mappers


def test_core_tables_are_registered():
    expected_tables = {
        "users",
        "books",
        "chapters",
        "chapter_summaries",
        "story_profiles",
        "generation_tasks",
        "generation_artifacts",
        "script_projects",
        "script_segments",
        "llm_configs",
        "prompt_templates",
        "prompt_template_versions",
        "llm_call_logs",
        "export_records",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_model_relationships_can_be_configured():
    configure_mappers()
