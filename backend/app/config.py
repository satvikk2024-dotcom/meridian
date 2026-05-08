from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Loads configuration from environment variables and .env file.
    Precedence: real env vars > .env file > field defaults.
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # looks in project root first, then current dir
        env_file_encoding="utf-8",
        extra="ignore",  # silently drop unknown env vars instead of raising
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/meridian.db"

    # LLM
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"

    # Synthesizer override (can use a better model than agents)
    synthesizer_provider: str = ""
    synthesizer_model: str = ""

    # Caching
    cache_llm_calls: bool = True
    cache_source_fetches: bool = True
    cache_dir: str = "./data/cache"

    # Data sources
    newsapi_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "meridian/0.1"
    github_token: str = ""
    bse_user_agent: str = ""
    screener_enabled: bool = True


settings = Settings()
