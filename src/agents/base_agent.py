"""Base agent class with shared LLM interaction logic."""

import logging
from abc import ABC, abstractmethod

from ..llm.router import LLMRouter, TaskType
from ..graph.state import GrantState

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    name: str
    task_type: TaskType = "hebrew"

    def __init__(self, router: LLMRouter):
        self.router = router

    @abstractmethod
    async def run(self, state: GrantState) -> dict:
        """Execute agent logic and return state updates."""
        ...

    async def _generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = await self.router.generate(
            messages=messages,
            task_type=self.task_type,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(f"[{self.name}] Used provider: {response.provider}, model: {response.model}")
        return response.content

    async def _generate_structured(self, system_prompt: str, user_prompt: str, schema: type):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.router.generate_structured(
            messages=messages,
            schema=schema,
            task_type="structured",
        )
