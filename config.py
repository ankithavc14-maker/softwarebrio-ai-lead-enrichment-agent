from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    groq_api_key: str
    groq_model: str = "openai/gpt-oss-20b"

    tavily_api_key: str | None = None

    max_pages_per_domain: int = 7
    page_timeout_ms: int = 20_000
    max_chars_per_page: int = 6_000
    max_total_evidence_chars: int = 24_000
    crawl_delay_ms: int = 350
    max_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )