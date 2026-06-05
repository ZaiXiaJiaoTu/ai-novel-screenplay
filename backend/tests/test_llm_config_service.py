from app.core.security import decrypt_text, encrypt_text, mask_api_key
from app.services.llm_config_service import serialize_llm_config


def test_api_key_mask_and_encryption_round_trip():
    api_key = "sk-test-123456"

    encrypted = encrypt_text(api_key)

    assert encrypted != api_key
    assert decrypt_text(encrypted) == api_key
    assert mask_api_key(api_key) == "sk-******3456"


def test_serialize_llm_config_hides_api_key():
    class Config:
        id = 1
        provider = "DeepSeek"
        base_url = "https://api.deepseek.com"
        api_key_masked = "sk-******3456"
        model_name = "deepseek-chat"
        temperature = None
        top_p = None
        max_tokens = 4096
        timeout_seconds = 60
        retry_count = 2
        task_scope = ["script_yaml_generation"]
        is_default = True
        enabled = True

    result = serialize_llm_config(Config())

    assert result.config_id == 1
    assert result.api_key_masked == "sk-******3456"
    assert not hasattr(result, "api_key")
