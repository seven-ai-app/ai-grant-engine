import logging
from typing import Literal

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
                "לא הוגדר אף ספק LLM. יש להגדיר לפחות מפתח API אחד בהגדרות."
            )

    def _get_priority_providers(self, task_type: TaskType) -> list[LLMProvider]:
        """Return providers in priority order, all available ones."""
        priority = self.settings.get_priority_list(task_type)
        ordered = []
        # First: providers in priority order
        for name in priority:
            p = self._providers.get(name)
            if p and p.is_available():
                ordered.append(p)
        # Then: any remaining providers not in priority list
        for p in self._providers.values():
            if p not in ordered and p.is_available():
                ordered.append(p)
        return ordered

    async def generate(
        self,
        messages: list[dict[str, str]],
        task_type: TaskType = "hebrew",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """Try each provider in order, fall back on failure."""
        providers = self._get_priority_providers(task_type)
        if not providers:
            raise RuntimeError("לא נמצאו ספקי LLM זמינים. יש להגדיר מפתח API בהגדרות.")

        last_error = None
        for provider in providers:
            try:
                logger.info(f"Trying provider: {provider.name}")
                return await provider.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                last_error = e
                continue  # Try next provider

        raise RuntimeError(
            f"כל ספקי ה-LLM נכשלו. שגיאה אחרונה: {last_error}\n"
            "בדוק שמפתח ה-API תקין."
        )

    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: type,
        task_type: TaskType = "structured",
        **kwargs,
    ):
        """Try each provider for structured output."""
        providers = self._get_priority_providers(task_type)
        if not providers:
            raise RuntimeError("לא נמצאו ספקי LLM זמינים.")

        last_error = None
        for provider in providers:
            try:
                return await provider.generate_structured(
                    messages=messages, schema=schema, **kwargs
                )
            except Exception as e:
                logger.warning(f"Provider {provider.name} structured failed: {e}")
                last_error = e
                continue

        raise RuntimeError(f"כל ספקי ה-LLM נכשלו לייצר output מובנה: {last_error}")
