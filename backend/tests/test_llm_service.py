from types import SimpleNamespace

from app.services.llm_service import (
    build_chat_model,
    call_llm_for_task,
    extract_response_text,
    render_prompt,
    summarize_text,
)
from app.core.security import encrypt_text


def test_render_prompt_replaces_variables():
    assert render_prompt("生成 {{title}} 的剧本", {"title": "长夜来信"}) == "生成 长夜来信 的剧本"


def test_summarize_text_collapses_and_truncates():
    result = summarize_text("a\n\n b " + "c" * 20, limit=10)

    assert result == "a b cccccc..."


def test_extract_response_text_reads_content():
    response = SimpleNamespace(content="模型输出")

    assert extract_response_text(response) == "模型输出"


def test_build_chat_model_omits_none_optional_parameters():
    config = SimpleNamespace(
        api_key_encrypted=encrypt_text("sk-test"),
        base_url="https://api.deepseek.com",
        model_name="deepseek-chat",
        temperature=None,
        top_p=None,
        max_tokens=None,
        timeout_seconds=60,
        retry_count=2,
    )

    model = build_chat_model(config)

    assert model.model_name == "deepseek-chat"


def test_call_llm_for_task_records_success_log():
    class FakeDb:
        def __init__(self):
            self.objects = []
            self.committed = False

        def add(self, obj):
            self.objects.append(obj)

        def commit(self):
            self.committed = True

    class FakeModel:
        def invoke(self, messages):
            assert messages[0][0] == "system"
            assert messages[1][1] == "请生成 长夜来信"
            return SimpleNamespace(content="生成结果")

    db = FakeDb()
    template = SimpleNamespace(
        id=1,
        system_prompt="你是编剧",
        user_prompt_template="请生成 {{title}}",
    )
    config = SimpleNamespace(id=2)

    import app.services.llm_service as service

    old_template = service.find_enabled_prompt_template
    old_config = service.find_llm_config
    service.find_enabled_prompt_template = lambda _db, _task_type: template
    service.find_llm_config = lambda _db, _task_type: config
    try:
        result = call_llm_for_task(
            db,
            task_type="script_episode_generation",
            variables={"title": "长夜来信"},
            model_factory=lambda _config: FakeModel(),
        )
    finally:
        service.find_enabled_prompt_template = old_template
        service.find_llm_config = old_config

    assert result == "生成结果"
    assert db.committed is True
    assert db.objects[0].status == "success"
    assert db.objects[0].response_summary == "生成结果"
