from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES


def test_default_prompts_include_active_generation_chain_tasks():
    task_types = {item["task_type"] for item in DEFAULT_PROMPT_TEMPLATES}

    assert "plot_event_split_generation" in task_types
    assert "script_episode_generation" in task_types
    assert "style_strategy_generation" in task_types
    assert "scene_plan_generation" in task_types
    assert "script_yaml_generation" in task_types
    assert "yaml_repair" in task_types
    assert "story_profile_generation" not in task_types
    assert "chapter_summary_generation" not in task_types


def test_default_script_yaml_prompt_requires_yaml_only():
    script_yaml_prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_yaml_generation"
    )

    assert script_yaml_prompt["output_format"] == "yaml"
    assert "Return YAML only" in script_yaml_prompt["system_prompt"]
