"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


class Settings(BaseSettings):
    """Runtime settings.

    Values are read from the process environment or backend/.env. Secrets must
    never be committed; only .env.example is tracked.

    Preferred database configuration uses separate DB_* fields. SQLAlchemy's
    URL.create() handles special characters such as @, :, /, and # without
    manual percent-encoding. DATABASE_URL remains available as an optional
    full-URL override for deployment environments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "PharmaPulse"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # Optional full URL override. If set, it takes precedence over DB_* fields.
    database_url: str | None = None

    # Preferred, encoding-safe database configuration.
    db_driver: str = "postgresql+psycopg"
    db_host: str = "localhost"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = "pharmapulse"
    db_user: str = "pharmapulse"
    db_password: str = ""

    cors_origins: str = "http://localhost:5173"

    max_upload_size_mb: int = Field(default=5, ge=1, le=100)
    max_import_rows: int = Field(default=50_000, ge=1)

    @property
    def sqlalchemy_url(self) -> URL:
        """Build a SQLAlchemy URL without requiring manual password encoding."""

        if self.database_url and self.database_url.strip():
            return make_url(self.database_url.strip())

        return URL.create(
            drivername=self.db_driver,
            username=self.db_user or None,
            password=self.db_password or None,
            host=self.db_host or None,
            port=self.db_port,
            database=self.db_name or None,
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
