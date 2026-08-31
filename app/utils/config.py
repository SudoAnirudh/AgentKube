from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None

    REDIS_URL: str = "redis://localhost:6379/2"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    MAX_RETRIES: int = 2
    AGENT_TIMEOUT_SECONDS: float = 30.0
    WORKER_CONCURRENCY: int = 1
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
