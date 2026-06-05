from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ai-novel-screenplay"
    app_version: str = "0.1.0"
    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_novel_screenplay"
    )
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
