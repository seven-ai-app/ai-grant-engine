import json
from pydantic import BaseModel
from ..provider import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if not self._client:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    async def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs) -> LLMResponse:
        client = self._get_client()
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        response = await client.generate_content_async(
            contents,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
        )
        return LLMResponse(
            content=response.text,
            model=self.model,
            provider=self.name,
            usage={},
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
        return 1_000_000

    def is_available(self) -> bool:
        return bool(self.api_key)
