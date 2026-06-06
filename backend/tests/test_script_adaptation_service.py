from types import SimpleNamespace

from app.services.script_adaptation_service import (
    build_adaptation_config,
    get_yaml_schema_delta,
    parse_json_payload,
    parse_yaml_payload,
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
