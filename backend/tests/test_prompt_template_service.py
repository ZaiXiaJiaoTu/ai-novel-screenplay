from types import SimpleNamespace

from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES
from app.services.prompt_template_service import (
    is_default_prompt_template,
    serialize_template,
    serialize_version,
    sync_default_prompt_template,
)


def test_serialize_prompt_template():
    template = SimpleNamespace(
        id=1,
        template_name="剧本 YAML 模板",
        task_type="script_episode_generation",
        system_prompt="系统提示词",
        user_prompt_template="用户提示词 {{scene_plan}}",
        output_format="yaml",
        variables=["scene_plan"],
        version=2,
        enabled=True,
    )

    result = serialize_template(template)

    assert result.template_id == 1
    assert result.version == 2
    assert result.variables == ["scene_plan"]


def test_serialize_prompt_template_version():
    version = SimpleNamespace(
        id=10,
        template_id=1,
        version=1,
        system_prompt="系统提示词",
        user_prompt_template="用户提示词",
        output_format="yaml",
        variables=["scene_plan"],
    )

    result = serialize_version(version)

    assert result.version_id == 10
    assert result.template_id == 1


def test_default_prompt_template_names_are_unique():
    names = [item["template_name"] for item in DEFAULT_PROMPT_TEMPLATES]

    assert len(names) == len(set(names))


def test_sync_default_prompt_template_updates_old_default():
    prompt_data = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "plot_event_split_generation"
    )
    template = SimpleNamespace(
        template_name="默认剧情事件拆分模板",
        system_prompt="旧系统提示词",
        user_prompt_template="旧用户提示词",
        output_format="json",
        variables=["book_title"],
        version=1,
    )

    changed = sync_default_prompt_template(template, prompt_data)

    assert changed is True
    assert template.version == 2
    assert template.system_prompt == prompt_data["system_prompt"]
    assert template.user_prompt_template == prompt_data["user_prompt_template"]
    assert template.variables == prompt_data["variables"]


def test_sync_default_prompt_template_keeps_version_when_unchanged():
    prompt_data = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "script_episode_generation"
    )
    template = SimpleNamespace(
        template_name=prompt_data["template_name"],
        system_prompt=prompt_data["system_prompt"],
        user_prompt_template=prompt_data["user_prompt_template"],
        output_format=prompt_data["output_format"],
        variables=prompt_data["variables"],
        version=3,
    )

    changed = sync_default_prompt_template(template, prompt_data)

    assert changed is False
    assert template.version == 3


def test_custom_prompt_template_is_not_treated_as_default():
    prompt_data = next(
        item
        for item in DEFAULT_PROMPT_TEMPLATES
        if item["task_type"] == "character_profile_consolidation"
    )
    template = SimpleNamespace(template_name="我的人物档案整合模板")

    assert is_default_prompt_template(template, prompt_data) is False
