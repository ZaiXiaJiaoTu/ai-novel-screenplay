from types import SimpleNamespace

from app.services.script_adaptation_service import (
    build_adaptation_config,
    build_episode_text_from_yaml,
    episode_payload_matches_source,
    get_yaml_schema_delta,
    normalize_episode_source_events,
    normalize_fact_content,
    parse_json_payload,
    parse_yaml_payload,
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
