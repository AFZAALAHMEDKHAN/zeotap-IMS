from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database URLs
    postgres_url: str = "postgresql+asyncpg://ims_user:ims_password@localhost:5432/ims_db"
    mongodb_url: str = "mongodb://ims_user:ims_password@localhost:27017/ims_signals?authSource=admin"
    redis_url: str = "redis://localhost:6379/0"

    # MongoDB database and collection names
    mongodb_db_name: str = "ims_signals"
    mongodb_signals_collection: str = "signals"
    mongodb_timeseries_collection: str = "timeseries"

    # Queue settings
    queue_max_size: int = 50000

    # Debounce window in seconds
    debounce_window_seconds: int = 10

    # Rate limiting (requests per minute per IP)
    rate_limit_per_minute: int = 600000

    # Metrics logging interval in seconds
    metrics_interval_seconds: int = 5

    # DB write retry settings
    db_write_max_retries: int = 3
    db_write_retry_backoff: float = 0.5

    # CORS allowed origins (comma-separated in env var, e.g. "https://a.com,https://b.com")
    cors_allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
