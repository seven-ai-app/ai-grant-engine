from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        ...

    @abstractmethod
    async def generate_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        temperature: float = 0.3,
        **kwargs,
    ) -> BaseModel:
        ...

    @abstractmethod
    def supports_hebrew(self) -> bool:
        ...

    @abstractmethod
    def context_window(self) -> int:
        ...

    @abstractmethod
    def is_available(self) -> bool:
        ...
