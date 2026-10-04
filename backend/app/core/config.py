from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    app_name: str = "Prism LLM Gateway"
    app_version: str = "0.1.0"
    environment: str = "development"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    huggingface_api_key: str = ""
    huggingface_base_url: str = ("https://router.huggingface.co/v1")
    
    prism_admin_key: str
    
    redis_url: str = "redis://localhost:6379/0"
    semantic_cache_enabled: bool = True
    semantic_cache_ttl: int = 3600
    semantic_cache_similarity_threshold: float = 0.90
    
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "prism"
    postgres_user: str = "postgres"
    postgres_password: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()