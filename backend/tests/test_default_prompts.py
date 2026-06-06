from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES


def test_default_prompts_include_active_generation_chain_tasks():
    task_types = {item["task_type"] for item in DEFAULT_PROMPT_TEMPLATES}

    assert "plot_event_split_generation" in task_types
    assert "script_episode_generation" in task_types
    assert "character_profile_consolidation" in task_types
    assert "style_strategy_generation" not in task_types
    assert "scene_plan_generation" not in task_types
    assert "script_yaml_generation" not in task_types
    assert "yaml_repair" not in task_types
    assert "story_profile_generation" not in task_types
    assert "chapter_summary_generation" not in task_types


def test_default_script_episode_prompt_requires_yaml_only():
    script_episode_prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )

    assert script_episode_prompt["output_format"] == "yaml"
    assert "只返回合法 YAML" in script_episode_prompt["system_prompt"]
    assert "禁止引入原文没有出现" in script_episode_prompt["system_prompt"]


def test_default_plot_event_prompt_is_chinese():
    plot_prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )

    assert "中文小说改编剧本" in plot_prompt["system_prompt"]
    assert "existing_characters" in plot_prompt["variables"]
    assert "禁止输出完整人物介绍" in plot_prompt["user_prompt_template"]
    assert "traits" in plot_prompt["user_prompt_template"]


def test_default_character_consolidation_prompt_is_chinese():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "character_profile_consolidation"
    )

    assert prompt["output_format"] == "json"
    assert "人物小传编辑" in prompt["system_prompt"]
    assert "关键特征、性格" in prompt["user_prompt_template"]
