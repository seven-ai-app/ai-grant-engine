import json
import httpx
from pydantic import BaseModel
from ..provider import LLMProvider, LLMResponse


class OpenRouterProvider(LLMProvider):
    name = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.1-70b-instruct:free"):
        self.api_key = api_key
        self.model = model

    async def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(self.BASE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})
        return LLMResponse(
            content=choice["message"]["content"],
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            raw=data,
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
        return 131_072

    def is_available(self) -> bool:
        return bool(self.api_key)
