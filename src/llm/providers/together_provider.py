import json
from pydantic import BaseModel
from ..provider import LLMProvider, LLMResponse


class TogetherProvider(LLMProvider):
    name = "together"

    def __init__(self, api_key: str, model: str = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self._client:
            from together import AsyncTogether
            self._client = AsyncTogether(api_key=self.api_key)
        return self._client

    async def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs) -> LLMResponse:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content,
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
            },
            raw=response,
        )

    async def generate_structured(self, messages, schema: type[BaseModel], temperature=0.3, **kwargs) -> BaseModel:
        system_msg = f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema.model_json_schema(), indent=2)}"
        augmented = [{"role": "system", "content": system_msg}] + messages
        response = await self.generate(augmented, temperature=temperature)
        data = json.loads(response.content)
        return schema.model_validate(data)

    def supports_hebrew(self) -> bool:
        return True

    def context_window(self) -> int:
        return 131_072

    def is_available(self) -> bool:
        return bool(self.api_key)
