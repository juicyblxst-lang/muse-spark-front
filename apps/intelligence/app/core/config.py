from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Muse API"
    api_version: str = "v1"
    environment: Literal["development", "test", "staging", "production"] = "development"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])

    # Supabase
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_service_role_key: SecretStr | None = None

    # Sibyl / storage
    sibyl_db_path: str = "./data/sibyl/muse.sqlite3"
    storage_bucket: str = "muse-documents"
    storage_root: str = "./data"

    # LLM / OpenClaw
    llm_provider: str = ""
    llm_api_key: SecretStr | None = None
    llm_model: str = ""
    openclaw_base_url: str = ""
    openclaw_api_key: SecretStr | None = None

    # Processing limits
    max_upload_bytes: int = 50 * 1024 * 1024
    max_processing_attempts: int = 3
    processing_timeout_seconds: int = 900
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"

    @field_validator("max_upload_bytes", "max_processing_attempts", "processing_timeout_seconds", "rate_limit_per_minute")
    @classmethod
    def positive_limits(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("processing limits must be positive")
        return value

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.environment != "production":
            return self

        required = {
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_PUBLISHABLE_KEY": self.supabase_publishable_key,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
            "LLM_API_KEY": self.llm_api_key,
            "LLM_MODEL": self.llm_model,
            "OPENCLAW_API_KEY": self.openclaw_api_key,
            "SIBYL_DB_PATH": self.sibyl_db_path,
        }
        missing = [name for name, value in required.items() if value is None or (isinstance(value, str) and not value.strip())]
        if missing:
            raise ValueError(f"Missing required production configuration: {', '.join(missing)}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
