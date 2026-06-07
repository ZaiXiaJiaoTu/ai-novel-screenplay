from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES


def test_default_prompts_include_all_four_task_types():
    task_types = {item["task_type"] for item in DEFAULT_PROMPT_TEMPLATES}

    assert "plot_event_split_generation" in task_types
    assert "script_episode_generation" in task_types
    assert "character_profile_consolidation" in task_types
    assert "script_episode_repair" in task_types
    assert "style_strategy_generation" not in task_types


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
        import re
        placeholders = set(re.findall(r"\{(\w+)\}", template))
        for var in declared:
            assert f"{{{var}}}" in template, (
                f"Variable {{{var}}} declared but not found in template "
                f"{item['template_name']}"
            )


# ── v2: plot event split template ──────────────────────────────────────


def test_default_plot_event_prompt_uses_facts_not_traits():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )

    assert "facts" in prompt["variables"] or '"facts"' in prompt["user_prompt_template"]
    assert '"traits"' not in prompt["user_prompt_template"]
    assert "trait_type" not in prompt["user_prompt_template"]


def test_plot_event_prompt_includes_aliases_in_output_schema():
    """v2: Output schema must include aliases field."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )
    assert '"aliases"' in prompt["user_prompt_template"]


def test_plot_event_prompt_no_longer_uses_atomic_event_term():
    """v2: "原子剧情事件" replaced with scene-relevant phrasing."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )
    assert "原子剧情事件" not in prompt["system_prompt"]
    assert "原子剧情事件" not in prompt["user_prompt_template"]
    assert "可独立用于剧本场景编排的剧情节点" in prompt["user_prompt_template"]


def test_plot_event_prompt_contains_fact_type_enum():
    """v2: fact_type restricted to the 9 allowed values."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )
    assert "fact_type只能是" in prompt["user_prompt_template"]
    assert "身份" in prompt["user_prompt_template"]
    assert "外貌" in prompt["user_prompt_template"]
    assert "当前状态" in prompt["user_prompt_template"]
    # Must NOT contain fuzzy example types
    assert "关键特征/性格" not in prompt["user_prompt_template"]


def test_plot_event_prompt_has_merge_rules():
    """v2: Events with same goal should be merged."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )
    assert "应合并为一个事件" in prompt["user_prompt_template"]


# ── v2: script episode generation template ─────────────────────────────


def test_script_episode_prompt_has_input_priority():
    """v2: Episode template must define input data responsibilities."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )

    assert "输入信息的职责" in prompt["system_prompt"]
    assert "剧情事件决定本集必须表现的剧情范围" in prompt["system_prompt"]
    assert "原文章节只用于补充" in prompt["system_prompt"]
    assert "人物档案只用于约束" in prompt["system_prompt"]


def test_script_episode_prompt_explicit_field_types():
    """v2: action=string[], transition=string, dialogue=object[]."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )
    assert "action必须是字符串数组" in prompt["user_prompt_template"]
    assert "transition必须是字符串" in prompt["user_prompt_template"]
    assert "dialogue必须是数组" in prompt["user_prompt_template"]


def test_script_episode_prompt_has_self_check():
    """v2: Self-check list before output."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )
    assert "输出前自行检查" in prompt["user_prompt_template"]
    assert "YAML是否可以安全解析" in prompt["user_prompt_template"]


def test_script_episode_prompt_has_ending_rules():
    """v2: Ending rules reference adaptation_config."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )
    assert "结尾规则" in prompt["user_prompt_template"]
    assert "ending_requirement" in prompt["user_prompt_template"]


def test_script_episode_prompt_forbids_markdown():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )
    assert "只返回合法YAML" in prompt["system_prompt"]
    assert "禁止Markdown代码块" in prompt["system_prompt"]
    assert "YAML锚点" in prompt["system_prompt"]


# ── v2: character consolidation template ───────────────────────────────


def test_character_consolidation_mentions_chronological_order():
    """v2: Facts are in chronological order, later facts are newer."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "character_profile_consolidation"
    )

    assert "按剧情发生顺序排列" in prompt["user_prompt_template"].replace(
        "按剧情顺序积累", "按剧情发生顺序排列"
    ) or "按剧情" in prompt["user_prompt_template"]
    assert "越靠后的事实通常越新" in prompt["user_prompt_template"]


def test_character_consolidation_distinguishes_transient_states():
    """v2: Must distinguish "正在恢复" vs "已经恢复"."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "character_profile_consolidation"
    )
    assert "正在恢复" in prompt["user_prompt_template"]
    assert "已经恢复" in prompt["user_prompt_template"]


def test_character_consolidation_has_temporal_rules():
    """v2: Historical states vs current states."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "character_profile_consolidation"
    )
    assert "曾经" in prompt["user_prompt_template"]


# ── v2: repair template ────────────────────────────────────────────────


def test_repair_template_has_yaml_parse_error_rules():
    """v2: Repair template handles YAML_PARSE_ERROR."""
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_repair"
    )
    assert "YAML_PARSE_ERROR" in prompt["user_prompt_template"]
    assert "缩进" in prompt["user_prompt_template"]


def test_repair_template_forbids_new_plot():
    prompt = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_repair"
    )
    assert "不得新增剧情" in prompt["system_prompt"] or "不得新增剧情" in prompt["user_prompt_template"]
    assert "不得虚构新事件" in prompt["user_prompt_template"]


# ── v2: generic IP restriction ─────────────────────────────────────────


def test_default_prompts_do_not_contain_hardcoded_external_ip():
    forbidden = ["哈利波特", "霍格沃茨", "格兰芬多", "斯莱特林",
                 "Harry Potter", "Hogwarts"]
    for item in DEFAULT_PROMPT_TEMPLATES:
        combined = item["system_prompt"] + item["user_prompt_template"]
        for marker in forbidden:
            assert marker not in combined, (
                f"Template {item['template_name']} contains "
                f"hardcoded external IP: {marker}"
            )
