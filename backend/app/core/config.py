from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ai-novel-screenplay"
    app_version: str = "0.1.0"
    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    database_url: str = Field(
        default="postgresql+psycopg://postgres@localhost:5432/ai_novel_screenplay"
    )
    secret_key: str = Field(default="ai-novel-screenplay-dev-secret-key")
    cors_origins: list[str] = ["http://127.0.0.1:5173", "http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.env == "production":
            if self.secret_key == "ai-novel-screenplay-dev-secret-key":
                raise ValueError("生产环境必须设置非默认 SECRET_KEY")
            if self.reload:
                raise ValueError("生产环境必须关闭 RELOAD")
        return self


settings = Settings()
