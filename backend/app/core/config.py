from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Muse API"
    api_version: str = "v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
