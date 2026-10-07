# print_factory_system/backend/app/core/config.py
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./print_factory.db"
    SANDBOX_DATABASE_URL: str = "sqlite:///./sandbox.db"
    DEBUG: bool = False
    ADMIN_PASSWORD_HASH: str = ""
    SESSION_HOURS: int = Field(default=12, ge=1, le=168)

    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
