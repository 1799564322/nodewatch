from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import __version__


class Settings(BaseSettings):
    app_name: str = "NodeWatch"
    app_env: str = "development"
    app_version: str = __version__
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://nodewatch:nodewatch@localhost:5432/nodewatch"
    secret_key: str = Field(min_length=32)
    session_cookie_name: str = "nodewatch_session"
    session_ttl_seconds: int = Field(default=604800, ge=300)
    session_cookie_secure: bool = False
    allowed_hosts: str = "localhost,127.0.0.1"
    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None
    default_collect_interval_seconds: int = Field(default=60, ge=10)
    max_agent_batch_samples: int = Field(default=500, ge=1, le=500)
    offline_after_seconds: int = Field(default=180, ge=30)
    raw_metric_retention_days: int = Field(default=30, ge=1)
    run_scheduler: bool = False

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
