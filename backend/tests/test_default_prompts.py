from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES


def test_default_prompts_include_all_four_task_types():
    task_types = {item["task_type"] for item in DEFAULT_PROMPT_TEMPLATES}

    assert "plot_event_split_generation" in task_types
    assert "script_episode_generation" in task_types
    assert "character_profile_consolidation" in task_types
    assert "script_episode_repair" in task_types
    # Removed legacy task types should not appear
    assert "style_strategy_generation" not in task_types
    assert "scene_plan_generation" not in task_types
    assert "script_yaml_generation" not in task_types
    assert "yaml_repair" not in task_types
    assert "story_profile_generation" not in task_types
    assert "chapter_summary_generation" not in task_types


def test_template_names_are_unique():
    names = [item["template_name"] for item in DEFAULT_PROMPT_TEMPLATES]
    assert len(names) == len(set(names))


def test_task_types_are_unique():
    types = [item["task_type"] for item in DEFAULT_PROMPT_TEMPLATES]
    assert len(types) == len(set(types))


def test_variables_match_actual_placeholders():
    for item in DEFAULT_PROMPT_TEMPLATES:
        template = item["user_prompt_template"] + item["system_prompt"]
        declared = set(item["variables"])
        # Check that all {var} placeholders have a declared variable
        import re
        placeholders = set(re.findall(r"\{(\w+)\}", template))
        # Some {key} used in JSON examples are not real variables
        real_placeholders = {
            p for p in placeholders
            if p in declared
        }
        for var in declared:
            assert f"{{{var}}}" in template, (
                f"Variable {{{var}}} declared but not found in template "
                f"{item['template_name']}"
            )


def test_default_script_episode_prompt_requires_yaml_only():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )

    assert prompt["output_format"] == "yaml"
    assert "只返回合法YAML" in prompt["system_prompt"]
    assert "禁止Markdown代码块" in prompt["system_prompt"]
    assert "YAML锚点" in prompt["system_prompt"]


def test_default_plot_event_prompt_uses_facts_not_traits():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )

    assert "中文小说剧情结构化分析助手" in prompt["system_prompt"]
    assert "existing_characters" in prompt["variables"]
    # Must use facts, not traits
    assert '"facts"' in prompt["user_prompt_template"]
    assert "fact_type" in prompt["user_prompt_template"]
    assert '"traits"' not in prompt["user_prompt_template"]
    assert "trait_type" not in prompt["user_prompt_template"]
    # Must include granularity constraints
    assert "40～120个汉字" in prompt["user_prompt_template"]
    assert "原子剧情事件" in prompt["system_prompt"]


def test_default_prompts_do_not_contain_hardcoded_external_ip():
    """P0.3: Prompt templates must not mention specific external works."""
    forbidden = ["哈利波特", "霍格沃茨", "格兰芬多", "斯莱特林",
                 "Harry Potter", "Hogwarts", "Gryffindor", "Slytherin"]
    for item in DEFAULT_PROMPT_TEMPLATES:
        combined = item["system_prompt"] + item["user_prompt_template"]
        for marker in forbidden:
            assert marker not in combined, (
                f"Template {item['template_name']} contains "
                f"hardcoded external IP: {marker}"
            )


def test_default_prompts_use_generic_ip_restriction():
    """P0.3: All templates should use the generic restriction phrase."""
    generic_phrase = (
        "不得引入输入材料中未出现的其他作品人物、地点、"
        "能力体系、专有名词或世界观设定"
    )
    for item in DEFAULT_PROMPT_TEMPLATES:
        combined = item["system_prompt"] + item["user_prompt_template"]
        assert generic_phrase in combined, (
            f"Template {item['template_name']} missing generic IP restriction"
        )


def test_default_character_consolidation_prompt_is_chinese():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "character_profile_consolidation"
    )

    assert prompt["output_format"] == "json"
    assert "人物档案编辑" in prompt["system_prompt"]
    assert "语义相同事实" in prompt["system_prompt"]
    assert "人物事实列表" in prompt["user_prompt_template"]
    # Input section uses "人物事实列表" as the variable key; output uses "profile"
    # The input data (characters var) uses facts, not traits
    assert '"traits"' not in prompt["user_prompt_template"]


def test_repair_template_exists_and_only_allows_fixes():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_repair"
    )

    assert prompt["output_format"] == "yaml"
    assert prompt["enabled"] is True
    assert "只修复格式" in prompt["system_prompt"]
    assert "不得新增剧情" in prompt["system_prompt"]
    assert "validation_errors" in prompt["variables"]
    assert "raw_output" in prompt["variables"]
    assert "yaml_schema" in prompt["variables"]


def test_script_episode_prompt_contains_event_coverage_rules():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )

    assert "每个输入事件必须至少被一个场景引用" in prompt["user_prompt_template"]
    assert "source_events只能使用本集输入事件的event_index" in prompt["user_prompt_template"]
    assert "不得使用数据库主键event_id" in prompt["user_prompt_template"]
    assert "scene_id从1开始连续递增" in prompt["user_prompt_template"]
    assert "dialogue必须是数组" in prompt["user_prompt_template"]


def test_plot_event_prompt_contains_fact_type_constraints():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )

    assert "fact_type限定为" in prompt["user_prompt_template"]
    assert "身份" in prompt["user_prompt_template"]
    assert "外貌" in prompt["user_prompt_template"]
    assert "当前状态" in prompt["user_prompt_template"]
    assert "没有新增人物事实时返回空数组" in prompt["user_prompt_template"]
