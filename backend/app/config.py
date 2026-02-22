"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings from environment."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ratemaster"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    market_refresh_minutes: int = 30
    api_cache_ttl_seconds: int = 60
    rate_limit_per_minute: int = 120
    uploads_dir: str = "uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
