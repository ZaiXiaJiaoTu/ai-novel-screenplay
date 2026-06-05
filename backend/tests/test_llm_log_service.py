from datetime import datetime
from types import SimpleNamespace

from app.services.llm_log_service import list_llm_call_logs, serialize_log_detail, serialize_log_item


def test_serialize_log_item_omits_summaries():
    log = SimpleNamespace(
        id=1,
        task_id=2,
        llm_config_id=3,
        prompt_template_id=4,
        task_type="script_yaml_generation",
        status="success",
        input_tokens=10,
        output_tokens=20,
        total_tokens=30,
        latency_ms=123,
        created_at=datetime(2026, 6, 5),
        request_summary="request",
        response_summary="response",
        error_message=None,
    )

    result = serialize_log_item(log)

    assert result.log_id == 1
    assert not hasattr(result, "request_summary")


def test_serialize_log_detail_includes_summaries():
    log = SimpleNamespace(
        id=1,
        task_id=2,
        llm_config_id=3,
        prompt_template_id=4,
        task_type="script_yaml_generation",
        status="failed",
        input_tokens=None,
        output_tokens=None,
        total_tokens=None,
        latency_ms=123,
        created_at=datetime(2026, 6, 5),
        request_summary="request",
        response_summary=None,
        error_message="timeout",
    )

    result = serialize_log_detail(log)

    assert result.request_summary == "request"
    assert result.error_message == "timeout"


def test_list_llm_call_logs_filters_by_task_id():
    class FakeScalars:
        def all(self):
            return []

    class FakeDb:
        def __init__(self):
            self.list_stmt = None
            self.count_stmt = None

        def scalars(self, stmt):
            self.list_stmt = stmt
            return FakeScalars()

        def scalar(self, stmt):
            self.count_stmt = stmt
            return 0

    db = FakeDb()

    result = list_llm_call_logs(db, task_id=7)

    assert result.total == 0
    assert "llm_call_logs.task_id" in str(db.list_stmt)
    assert "llm_call_logs.task_id" in str(db.count_stmt)
