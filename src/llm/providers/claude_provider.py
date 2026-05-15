import json
from pydantic import BaseModel
from ..provider import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self._client:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs) -> LLMResponse:
        client = self._get_client()
        # Extract system message
        system = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system += msg["content"] + "\n"
            else:
                chat_messages.append(msg)

        if not chat_messages:
            chat_messages = [{"role": "user", "content": "Please proceed."}]

        response = await client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system.strip() if system else None,
            messages=chat_messages,
        )
        content = response.content[0].text
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
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
        return 200_000

    def is_available(self) -> bool:
        return bool(self.api_key)
