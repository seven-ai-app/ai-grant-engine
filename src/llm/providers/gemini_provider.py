import asyncio
import json
import logging
from pydantic import BaseModel
from ..provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def _build_contents(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        """Convert OpenAI-style messages to Gemini format.

        Returns (system_instruction, contents_list).
        Gemini requires:
        - First message must be 'user' role
        - Alternating user/model turns
        - System messages extracted separately
        """
        system_parts = []
        contents = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_parts.append(content)
                continue

            gemini_role = "user" if role == "user" else "model"

            # Merge consecutive same-role messages
            if contents and contents[-1]["role"] == gemini_role:
                contents[-1]["parts"][0]["text"] += "\n\n" + content
            else:
                contents.append({"role": gemini_role, "parts": [{"text": content}]})

        # Gemini requires first turn to be 'user'
        if contents and contents[0]["role"] == "model":
            contents.insert(0, {"role": "user", "parts": [{"text": "Please continue."}]})

        # If no user messages at all, add a placeholder
        if not contents:
            contents = [{"role": "user", "parts": [{"text": "Please respond."}]}]

        system_instruction = "\n\n".join(system_parts) if system_parts else None
        return system_instruction, contents

    def _sync_generate(self, messages: list[dict], temperature: float, max_tokens: int) -> str:
        """Synchronous Gemini call - will be run in thread."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)

        system_instruction, contents = self._build_contents(messages)

        kwargs = {}
        if system_instruction:
            kwargs["system_instruction"] = system_instruction

        model = genai.GenerativeModel(self.model, **kwargs)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = model.generate_content(
            contents,
            generation_config=generation_config,
        )

        # Check for blocked response
        if not response.candidates:
            raise RuntimeError("Gemini returned no candidates (possibly blocked by safety filters)")

        candidate = response.candidates[0]
        if hasattr(candidate, "finish_reason") and str(candidate.finish_reason) not in ("STOP", "1", "FinishReason.STOP"):
            logger.warning(f"Gemini finish_reason: {candidate.finish_reason}")

        return response.text

    async def generate(self, messages, temperature=0.7, max_tokens=4096, **kwargs) -> LLMResponse:
        try:
            text = await asyncio.to_thread(
                self._sync_generate, messages, temperature, max_tokens
            )
            return LLMResponse(
                content=text,
                model=self.model,
                provider=self.name,
                usage={},
                raw=None,
            )
        except Exception as e:
            logger.error(f"Gemini generate error: {e}")
            raise

    async def generate_structured(self, messages, schema: type[BaseModel], temperature=0.3, **kwargs) -> BaseModel:
        system_msg = (
            f"Respond ONLY with valid JSON matching this schema. "
            f"No markdown, no explanation, just raw JSON:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}"
        )
        augmented = [{"role": "system", "content": system_msg}] + list(messages)
        response = await self.generate(augmented, temperature=temperature)
        text = response.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.endswith("```"):
                text = text[: text.rfind("```")]
        data = json.loads(text)
        return schema.model_validate(data)

    def supports_hebrew(self) -> bool:
        return True

    def context_window(self) -> int:
        return 1_000_000

    def is_available(self) -> bool:
        return bool(self.api_key)
