"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the S&P 500 News Sentiment Curator."""

    # Database
    database_url: str = "postgresql+asyncpg://newsuser:changeme@postgres:5432/sp500news"
    redis_url: str = "redis://redis:6379"

    # LLM Provider — one of: lmstudio | gemini | openrouter | anthropic
    llm_provider: str = "lmstudio"
    llm_model: str = "mistral"

    # LM Studio
    lmstudio_base_url: str = "http://host.docker.internal:1234/v1"

    # External API keys (only needed for their respective provider)
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""

    # News data sources
    newsapi_key: str = ""

    # FinBERT
    finbert_model: str = "ProsusAI/finbert"
    finbert_cache_dir: str = "/app/model_cache"
    finbert_neutral_threshold: float = 0.85

    # Pipeline
    ingest_interval_minutes: int = 30
    max_concurrent_llm_calls: int = 1
    max_article_body_chars: int = 3000
    llm_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
