from pydantic import SecretStr

from xiaosu.agent.model import DashScopeChatModel, ZhipuChatModel, create_chat_model
from xiaosu.core.config import Settings
from xiaosu.core.runtime import RuntimeConfiguration
from xiaosu.knowledge.embeddings import (
    DashScopeEmbeddingClient,
    ZhipuEmbeddingClient,
    create_embedding_client,
)


def test_qwen_models_are_the_safe_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.llm_provider == "dashscope"
    assert settings.embedding_provider == "dashscope"
    assert settings.llm_model == "qwen3.7-plus"
    assert settings.embedding_model == "qwen3.7-text-embedding"
    assert settings.embedding_dimension == 1024
    assert settings.dashscope_base_url.startswith("https://")


def test_dashscope_key_is_not_required_for_mock_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.dashscope_api_key is None
    assert settings.zhipuai_api_key is None


def test_runtime_configuration_applies_persisted_admin_settings() -> None:
    settings = Settings(_env_file=None)
    runtime = RuntimeConfiguration(
        llm_provider="dashscope",
        llm_model="qwen-max",
        chunk_size=900,
        chunk_overlap=150,
        retrieval_top_k=8,
        retrieval_min_score=0.42,
        max_upload_mb=35,
        embedding_batch_size=12,
        duplicate_policy="skip",
    )

    runtime.apply(settings)

    assert settings.llm_provider == "dashscope"
    assert settings.llm_model == "qwen-max"
    assert settings.max_upload_bytes == 35 * 1024 * 1024
    assert settings.embedding_batch_size == 12
    assert settings.duplicate_policy == "skip"


def test_multi_provider_zhipuai_switch_and_factories() -> None:
    settings = Settings(
        _env_file=None,
        dashscope_api_key=SecretStr("mock-ds-key"),
        zhipuai_api_key=SecretStr("mock-zhipu-key"),
    )

    # 1. 默认百炼对话模型
    chat_model = create_chat_model(settings)
    assert isinstance(chat_model, DashScopeChatModel)

    # 2. 切换至智谱清言运行时
    runtime = RuntimeConfiguration(
        llm_provider="zhipuai",
        llm_model="glm-4-plus",
        chunk_size=700,
        chunk_overlap=100,
        retrieval_top_k=5,
        retrieval_min_score=0.35,
        max_upload_mb=20,
        embedding_batch_size=10,
        duplicate_policy="replace",
    )
    runtime.apply(settings)

    assert settings.llm_provider == "zhipuai"
    assert settings.llm_model == "glm-4-plus"

    zhipu_chat = create_chat_model(settings)
    assert isinstance(zhipu_chat, ZhipuChatModel)

    # 3. 验证 Embedding 工厂
    assert isinstance(create_embedding_client(settings), DashScopeEmbeddingClient)
    settings.embedding_provider = "zhipuai"
    assert isinstance(create_embedding_client(settings), ZhipuEmbeddingClient)
