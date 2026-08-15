from collections.abc import Sequence

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from xiaosu.core.config import Settings


class ModelConfigurationError(RuntimeError):
    pass


class DashScopeEmbeddingClient:
    def __init__(self, settings: Settings) -> None:
        secret = settings.dashscope_api_key
        if secret is None or not secret.get_secret_value():
            raise ModelConfigurationError("请先在本机 .env 填写 DASHSCOPE_API_KEY")
        self._model = settings.embedding_model
        self._dimension = settings.embedding_dimension
        self._client = AsyncOpenAI(
            api_key=secret.get_secret_value(),
            base_url=settings.dashscope_base_url,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._model,
            input=list(texts),
            dimensions=self._dimension,
            encoding_format="float",
        )
        return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]
