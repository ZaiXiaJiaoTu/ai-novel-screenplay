from types import SimpleNamespace

from app.services.script_adaptation_service import (
    _derive_adaptation_targets,
    build_adaptation_config,
    build_episode_text_from_yaml,
    episode_payload_matches_source,
    get_yaml_schema_delta,
    normalize_character_facts_payload,
    normalize_episode_metadata,
    normalize_episode_source_events,
    normalize_fact_content,
    parse_json_payload,
    parse_yaml_payload,
    select_relevant_characters,
    serialize_character,
)


def test_yaml_schema_delta_differs_by_adaptation_type():
    tv_delta = get_yaml_schema_delta("tv")
    audio_delta = get_yaml_schema_delta("audio_drama")

    assert tv_delta["metadata"]["format"] == "episode"
    assert audio_delta["metadata"]["format"] == "audio_drama_episode"
    assert "soundscape" in audio_delta["scene_extra"]


def test_build_adaptation_config_contains_prompt_parameters():
    project = SimpleNamespace(
        script_type="short_drama",
        default_target_duration=5,
        pacing="fast",
        scene_frequency="high",
        dialogue_density="low",
        events_per_episode=8,
        yaml_schema_delta=None,
    )

    config = build_adaptation_config(project)

    assert config["adaptation_type_label"] == "短剧"
    assert config["episode_duration"] == 5
    assert config["pacing_label"] == "快"
    assert config["scene_frequency_label"] == "高"
    assert config["dialogue_density_label"] == "低"
    assert config["events_per_episode"] == 8
    assert config["yaml_schema_delta"]["metadata"]["hook_required"] is True


def test_parse_json_payload_accepts_code_fence():
    payload = parse_json_payload('```json\n{"events": [], "characters": []}\n```')

    assert payload == {"events": [], "characters": []}


def test_parse_yaml_payload_accepts_code_fence():
    payload = parse_yaml_payload("```yaml\nscript:\n  metadata:\n    title: test\n```")

    assert payload["script"]["metadata"]["title"] == "test"


def test_episode_text_export_renders_yaml_content():
    text = build_episode_text_from_yaml(
        """
script:
  metadata:
    title: 第一集
  scenes:
    - scene_id: S1
      scene_title: 觉醒
      action:
        - 唐三走进武魂殿。
      dialogue:
        - speaker: 唐三
          line: 我会变强。
"""
    )

    assert "《第一集》" in text
    assert "场景 S1：觉醒" in text
    assert "动作：" in text
    assert "唐三：我会变强。" in text


def test_episode_payload_rejects_off_topic_external_ip():
    payload = {
        "script": {
            "metadata": {"source_book_title": "斗罗大陆"},
            "scenes": [{"action": ["哈利波特走进霍格沃茨。"]}],
        }
    }

    assert episode_payload_matches_source(
        payload,
        book_title="斗罗大陆",
        source_text="斗罗大陆 唐三 武魂 蓝银草",
    ) is False


def test_episode_source_events_use_global_plot_event_numbers():
    events = [
        SimpleNamespace(id=101, event_index=17),
        SimpleNamespace(id=102, event_index=18),
    ]
    payload = {
        "script": {
            "scenes": [
                {"source_events": [17]},
                {"source_events": [102]},
                {"source_events": [2]},
            ]
        }
    }

    result = normalize_episode_source_events(payload, events)

    assert result["script"]["scenes"][0]["source_events"] == [17]
    assert result["script"]["scenes"][1]["source_events"] == [18]
    assert result["script"]["scenes"][2]["source_events"] == [18]


def test_episode_metadata_is_normalized_to_project_config():
    project = SimpleNamespace(
        script_type="animation",
        default_target_duration=24,
        pacing="medium",
        scene_frequency="medium",
        dialogue_density="medium",
        yaml_schema_delta={"metadata": {"format": "animation_episode"}},
    )
    events = [SimpleNamespace(id=1, event_index=17, content="唐三前往诺丁城，开始新的修行。")]
    payload = {
        "script": {
            "metadata": {
                "title": "斗罗大陆 第6集：启程·诺丁城",
                "episode_number": 99,
                "source_book_title": "错误书名",
                "script_type": "old",
                "target_duration": 10,
            },
            "scenes": [{"scene_title": "启程·诺丁城"}],
        }
    }

    result = normalize_episode_metadata(
        payload,
        project,
        episode_number=6,
        book_title="斗罗大陆",
        events=events,
    )

    assert result["script"]["metadata"] == {
        "format": "animation_episode",
        "title": "启程·诺丁城",
        "episode_number": 6,
        "source_book_title": "斗罗大陆",
        "adaptation_type": "animation",
        "episode_duration": 24,
        "pacing": "medium",
        "scene_frequency": "medium",
        "dialogue_density": "medium",
    }


def test_episode_metadata_title_falls_back_to_scene_title():
    project = SimpleNamespace(
        script_type="animation",
        default_target_duration=24,
        pacing="medium",
        scene_frequency="medium",
        dialogue_density="medium",
        yaml_schema_delta={"metadata": {"format": "animation_episode"}},
    )
    payload = {
        "script": {
            "metadata": {"title": "斗罗大陆 第1集"},
            "scenes": [{"scene_title": "废武魂与先天满魂力"}],
        }
    }

    result = normalize_episode_metadata(
        payload,
        project,
        episode_number=1,
        book_title="斗罗大陆",
        events=[],
    )

    assert result["script"]["metadata"]["title"] == "废武魂与先天满魂力"


def test_fact_normalization_removes_punctuation_for_deduping():
    assert normalize_fact_content("唐三之母，十万年蓝银皇。") == normalize_fact_content(
        "唐三之母 十万年蓝银皇"
    )


def test_serialized_character_prefers_consolidated_profile():
    character = SimpleNamespace(
        id=1,
        name="唐三",
        profile="1. 碎片化特征",
        metadata_json={"consolidated_profile": "唐三，坚韧谨慎，重视亲情。"},
    )

    result = serialize_character(character)

    assert result.profile == "唐三，坚韧谨慎，重视亲情。"


# ── normalize_character_facts_payload ──────────────────────────────


def test_normalize_old_traits_format_to_facts():
    """P0.1: Old format with 'traits' and 'trait_type' is normalized to 'facts'."""
    item = {
        "name": "唐三",
        "traits": [
            {"trait_type": "身份", "content": "圣魂村孩子"},
            {"trait_type": "能力", "content": "蓝银草武魂"},
        ],
    }

    result = normalize_character_facts_payload(item)

    assert result["name"] == "唐三"
    assert "facts" in result
    assert "traits" not in result
    assert result["facts"][0]["fact_type"] == "身份"
    assert result["facts"][0]["content"] == "圣魂村孩子"
    assert result["facts"][1]["fact_type"] == "能力"
    assert result["facts"][1]["content"] == "蓝银草武魂"


def test_normalize_new_facts_format_passes_through():
    """P0.1: New format with 'facts' and 'fact_type' remains unchanged."""
    item = {
        "name": "小舞",
        "facts": [
            {"fact_type": "身份", "content": "诺丁学院学生"},
        ],
    }

    result = normalize_character_facts_payload(item)

    assert result["name"] == "小舞"
    assert result["facts"] == [{"fact_type": "身份", "content": "诺丁学院学生"}]


def test_normalize_features_format_to_facts():
    """P0.1: Old 'features' format is also normalized."""
    item = {
        "name": "大师",
        "features": [
            {"feature_type": "身份", "content": "诺丁学院老师"},
        ],
    }

    result = normalize_character_facts_payload(item)

    assert result["facts"][0]["fact_type"] == "身份"
    assert result["facts"][0]["content"] == "诺丁学院老师"


def test_normalize_string_fact_items():
    """String fact items get default fact_type."""
    item = {
        "name": "唐三",
        "traits": ["蓝银草武魂觉醒", "先天满魂力"],
    }

    result = normalize_character_facts_payload(item)

    assert result["facts"][0]["fact_type"] == "关键特征"
    assert result["facts"][0]["content"] == "蓝银草武魂觉醒"
    assert result["facts"][1]["content"] == "先天满魂力"


def test_normalize_empty_name_returns_empty_string():
    """Empty or missing name produces empty string."""
    result = normalize_character_facts_payload({})
    assert result["name"] == ""


def test_normalize_fallback_profile_to_facts():
    """When only profile exists, it becomes a single fact with fact_type='设定'."""
    item = {"name": "玉小刚", "profile": "武魂理论大师，人称大师。"}

    result = normalize_character_facts_payload(item)

    assert result["facts"][0]["fact_type"] == "设定"
    assert result["facts"][0]["content"] == "武魂理论大师，人称大师。"


def test_normalize_no_facts_returns_empty_list():
    """No facts, traits, features, or profile results in empty facts list."""
    item = {"name": "Unknown"}

    result = normalize_character_facts_payload(item)

    assert result["facts"] == []


def test_normalize_mixed_fact_keys():
    """Mixed key types in facts are resolved per-fact."""
    item = {
        "name": "唐三",
        "facts": [
            {"fact_type": "身份", "content": "圣魂村孩子"},
            {"trait_type": "能力", "content": "蓝银草武魂"},
            {"type": "物品", "content": "玄天宝鉴"},
        ],
    }

    result = normalize_character_facts_payload(item)

    assert result["facts"][0]["fact_type"] == "身份"
    assert result["facts"][1]["fact_type"] == "能力"
    assert result["facts"][2]["fact_type"] == "物品"


# ── build_adaptation_config (P1.3) ───────────────────────────────────


def test_adaptation_config_includes_derived_targets():
    """P1.3: build_adaptation_config returns explicit numeric targets."""
    project = SimpleNamespace(
        script_type="short_drama",
        default_target_duration=5,
        pacing="fast",
        scene_frequency="high",
        dialogue_density="medium",
        events_per_episode=8,
        yaml_schema_delta=None,
    )

    config = build_adaptation_config(project)

    assert "target_scene_count" in config
    assert "dialogue_ratio" in config
    assert "scene_length_hint" in config
    assert "ending_requirement" in config
    assert config["target_scene_count"]["min"] >= 1
    assert config["target_scene_count"]["max"] >= config["target_scene_count"]["min"]
    assert 0 <= config["dialogue_ratio"]["min"] <= config["dialogue_ratio"]["max"] <= 1


def test_derive_targets_scene_count_scales_with_frequency():
    low = _derive_adaptation_targets(
        {"scene_frequency": "low", "events_per_episode": 10, "pacing": "medium", "dialogue_density": "medium", "episode_duration": 5, "adaptation_type": "tv"}
    )
    high = _derive_adaptation_targets(
        {"scene_frequency": "high", "events_per_episode": 10, "pacing": "medium", "dialogue_density": "medium", "episode_duration": 5, "adaptation_type": "tv"}
    )
    assert high["target_scene_count"]["max"] > low["target_scene_count"]["max"]


def test_derive_targets_ending_differs_by_type():
    tv = _derive_adaptation_targets(
        {"adaptation_type": "tv", "episode_duration": 5, "pacing": "medium", "scene_frequency": "medium", "dialogue_density": "medium", "events_per_episode": 5}
    )
    short = _derive_adaptation_targets(
        {"adaptation_type": "short_drama", "episode_duration": 5, "pacing": "medium", "scene_frequency": "medium", "dialogue_density": "medium", "events_per_episode": 5}
    )
    assert tv["ending_requirement"] != short["ending_requirement"]


# ── select_relevant_characters (P1.1) ──────────────────────────────────


def _make_char_detail(name: str, *, aliases: list[str] | None = None) -> SimpleNamespace:
    meta = {}
    if aliases:
        meta["aliases"] = aliases
    return SimpleNamespace(
        character_id=hash(name) % 10000,
        name=name,
        profile=f"{name}的档案",
        metadata_json=meta,
    )


def _make_chapter(index: int, title: str, content: str) -> SimpleNamespace:
    return SimpleNamespace(chapter_index=index, title=title, content=content)


def _make_event(index: int, content: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=100 + index, batch_id=1, event_index=index,
        content=content, source_chapter_start=1, source_chapter_end=1,
        locked=False,
    )


def test_select_characters_by_event_content():
    characters = [
        _make_char_detail("Alice"),
        _make_char_detail("Bob"),
        _make_char_detail("Charlie"),
    ]
    events = [_make_event(1, "Alice and Bob walked into the room.")]
    chapters = []

    result = select_relevant_characters(characters, events, chapters)

    names = {c.name for c in result}
    assert "Alice" in names
    assert "Bob" in names
    assert "Charlie" not in names


def test_select_characters_by_chapter_content():
    characters = [_make_char_detail("Master"), _make_char_detail("Alice")]
    events = []
    chapters = [_make_chapter(1, "Master's Guidance", "Master taught Alice the theory.")]

    result = select_relevant_characters(characters, events, chapters)

    names = {c.name for c in result}
    assert "Master" in names
    assert "Alice" in names


def test_select_characters_by_alias():
    """P1.2: Characters are matched by alias if name doesn't appear in corpus."""
    characters = [
        _make_char_detail("Alice", aliases=["Ali", "Ally"]),
    ]
    events = [_make_event(1, "Ali walked onto the stage.")]
    chapters = []

    result = select_relevant_characters(characters, events, chapters)

    assert len(result) == 1
    assert result[0].name == "Alice"


def test_select_characters_includes_core_when_few_matched():
    """When no characters match, at most 3 are included as fallback."""
    characters = [
        _make_char_detail("Alice"),
        _make_char_detail("Bob"),
        _make_char_detail("Charlie"),
        _make_char_detail("Diana"),
    ]
    events = [_make_event(1, "The sun is shining.")]  # no character names
    chapters = []

    result = select_relevant_characters(characters, events, chapters)

    assert 1 <= len(result) <= 3


def test_select_characters_respects_max_limit():
    characters = [_make_char_detail(f"Char{i}") for i in range(50)]
    events = [_make_event(i, f"Char{i} appears.") for i in range(50)]
    chapters = []

    result = select_relevant_characters(characters, events, chapters, max_characters=30)

    assert len(result) == 30


def test_select_empty_characters_returns_empty():
    assert select_relevant_characters([], [], []) == []
