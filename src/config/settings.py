from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Free providers
    groq_api_key: str = ""
    gemini_api_key: str = ""
    together_api_key: str = ""
    openrouter_api_key: str = ""

    # Paid providers
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    mistral_api_key: str = ""

    # Provider priority (comma-separated)
    llm_priority_hebrew: str = "claude,openai,gemini,groq,together,openrouter,mistral"
    llm_priority_structured: str = "gemini,groq,together,openrouter,claude,openai,mistral"
    llm_priority_reasoning: str = "claude,openai,gemini,groq,mistral,together,openrouter"

    # Integrations
    github_token: str = ""
    chroma_db_path: str = "./chroma_db"

    # Output
    output_dir: str = "./output"

    def get_priority_list(self, task_type: str) -> list[str]:
        mapping = {
            "hebrew": self.llm_priority_hebrew,
            "structured": self.llm_priority_structured,
            "reasoning": self.llm_priority_reasoning,
        }
        raw = mapping.get(task_type, self.llm_priority_hebrew)
        return [p.strip() for p in raw.split(",")]

    def get_available_providers(self) -> dict[str, str]:
        providers = {}
        if self.groq_api_key:
            providers["groq"] = self.groq_api_key
        if self.gemini_api_key:
            providers["gemini"] = self.gemini_api_key
        if self.together_api_key:
            providers["together"] = self.together_api_key
        if self.openrouter_api_key:
            providers["openrouter"] = self.openrouter_api_key
        if self.anthropic_api_key:
            providers["claude"] = self.anthropic_api_key
        if self.openai_api_key:
            providers["openai"] = self.openai_api_key
        if self.mistral_api_key:
            providers["mistral"] = self.mistral_api_key
        return providers

    @property
    def output_path(self) -> Path:
        p = Path(self.output_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p
