from types import SimpleNamespace

from app.services.prompt_template_service import serialize_template, serialize_version
from app.prompts.default_prompts import DEFAULT_PROMPT_TEMPLATES


def test_serialize_prompt_template():
    template = SimpleNamespace(
        id=1,
        template_name="剧本 YAML 模板",
        task_type="script_yaml_generation",
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
