from sqlalchemy.orm import configure_mappers

from app import models  # noqa: F401
from app.core.database import Base


def test_core_tables_are_registered():
    expected_tables = {
        "users",
        "books",
        "chapters",
        "script_projects",
        "script_event_batches",
        "script_plot_events",
        "script_character_profiles",
        "script_character_facts",
        "script_episodes",
        "llm_configs",
        "prompt_templates",
        "prompt_template_versions",
        "llm_call_logs",
        "export_records",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())
    assert "chapter_summaries" not in Base.metadata.tables
    assert "story_profiles" not in Base.metadata.tables


def test_model_relationships_can_be_configured():
    configure_mappers()
