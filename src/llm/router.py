import logging
from typing import Literal

from tenacity import retry, stop_after_attempt, wait_exponential

from .provider import LLMProvider, LLMResponse
from .providers import (
    ClaudeProvider,
    GeminiProvider,
    GroqProvider,
    MistralProvider,
    OpenAIProvider,
    OpenRouterProvider,
    TogetherProvider,
)
from ..config.settings import Settings

logger = logging.getLogger(__name__)

TaskType = Literal["hebrew", "structured", "reasoning"]

PROVIDER_CLASSES: dict[str, type[LLMProvider]] = {
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "together": TogetherProvider,
    "openrouter": OpenRouterProvider,
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
    "mistral": MistralProvider,
}


class LLMRouter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._providers: dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self):
        available = self.settings.get_available_providers()
        for name, api_key in available.items():
            cls = PROVIDER_CLASSES.get(name)
            if cls:
                self._providers[name] = cls(api_key=api_key)
                logger.info(f"Initialized provider: {name}")

        if not self._providers:
            raise ValueError(
                "No LLM providers configured. Set at least one API key in .env"
            )

    def get_provider(self, task_type: TaskType = "hebrew") -> LLMProvider:
        priority = self.settings.get_priority_list(task_type)
        for name in priority:
            provider = self._providers.get(name)
            if provider and provider.is_available():
                return provider
        # Fallback to any available
        for provider in self._providers.values():
            if provider.is_available():
                return provider
        raise RuntimeError("No LLM providers available")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(
        self,
        messages: list[dict[str, str]],
        task_type: TaskType = "hebrew",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        provider = self.get_provider(task_type)
        try:
            return await provider.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"Provider {provider.name} failed: {e}, trying next")
            # Remove failed provider temporarily and retry
            self._providers.pop(provider.name, None)
            raise

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: type,
        task_type: TaskType = "structured",
        **kwargs,
    ):
        provider = self.get_provider(task_type)
        return await provider.generate_structured(messages=messages, schema=schema, **kwargs)
