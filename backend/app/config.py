from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Planora AI"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./projectintel.db"

    @field_validator("database_url", mode="after")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "OPENCODE_ZEN_API_KEY", "OPENCODE_API_KEY"),
    )
    gemini_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai",
        validation_alias=AliasChoices("GEMINI_BASE_URL", "GOOGLE_BASE_URL", "OPENAI_BASE_URL", "OPENCODE_ZEN_BASE_URL", "OPENCODE_BASE_URL"),
    )
    gemini_model: str = Field(
        default="gemini-3.1-flash-lite",
        validation_alias=AliasChoices("GEMINI_MODEL", "GOOGLE_MODEL", "OPENAI_MODEL", "OPENCODE_ZEN_MODEL", "OPENCODE_MODEL"),
    )

    @property
    def opencode_zen_api_key(self) -> str:
        return self.gemini_api_key

    @property
    def opencode_zen_base_url(self) -> str:
        return self.gemini_base_url

    @property
    def opencode_zen_model(self) -> str:
        return self.gemini_model

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_environment: str = "development"
    max_ai_tokens_per_request: int = 2048
    sensitive_data_action: str = "block"  # block | redact
    cors_origins: str = "http://localhost:5173"

    orchestration_mode: str = "workflow"  # workflow | agents

    project_memory_enabled: bool = True
    chroma_persist_path: str = "./chroma_data"
    project_similarity_threshold: float = 0.30

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 25


settings = Settings()
