import json
from pydantic import BaseModel
from ..provider import LLMProvider, LLMResponse


class MistralProvider(LLMProvider):
    name = "mistral"

    def __init__(self, api_key: str, model: str = "mistral-large-latest"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self._client:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
        return self._client

    async def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs) -> LLMResponse:
        client = self._get_client()
        response = await client.chat.complete_async(
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
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
            raw=response,
        )

    async def generate_structured(self, messages, schema: type[BaseModel], temperature=0.3, **kwargs) -> BaseModel:
        system_msg = f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema.model_json_schema(), indent=2)}"
        augmented = [{"role": "system", "content": system_msg}] + messages
        response = await self.generate(augmented, temperature=temperature)
        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(text)
        return schema.model_validate(data)

    def supports_hebrew(self) -> bool:
        return True

    def context_window(self) -> int:
        return 128_000

    def is_available(self) -> bool:
        return bool(self.api_key)
