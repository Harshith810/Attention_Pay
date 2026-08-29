from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "AttentionPay API"
    environment: str = "development"
    frontend_origin: str = "http://localhost:5173"

    database_url: str

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()