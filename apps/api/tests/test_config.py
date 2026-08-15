from xiaosu.core.config import get_settings


def test_qwen_models_are_the_safe_defaults() -> None:
    settings = get_settings()

    assert settings.llm_provider == "dashscope"
    assert settings.llm_model == "qwen3.7-plus"
    assert settings.embedding_model == "qwen3.7-text-embedding"
    assert settings.embedding_dimension == 1024
    assert settings.dashscope_base_url.startswith("https://")


def test_dashscope_key_is_not_required_for_mock_development() -> None:
    settings = get_settings()

    if settings.dashscope_api_key is not None:
        assert settings.dashscope_api_key.get_secret_value() == ""
