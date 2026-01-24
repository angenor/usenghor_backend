"""
Configuration de l'application
==============================

Gestion centralisée des variables d'environnement via Pydantic Settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application chargée depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_secret_key: str = "change-me-in-production"

    # Database
    postgres_user: str = "usenghor"
    postgres_password: str = "usenghor_secret"
    postgres_db: str = "usenghor"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    database_url: str | None = None

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Storage
    storage_type: Literal["local", "s3"] = "local"
    storage_path: str = "/var/www/uploads"

    # Email
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = "noreply@usenghor.org"
    smtp_password: str = ""

    @property
    def database_url_async(self) -> str:
        """Retourne l'URL de connexion PostgreSQL pour asyncpg."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Retourne l'URL de connexion PostgreSQL pour psycopg2 (migrations)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Retourne la liste des origines CORS."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        """Vérifie si l'environnement est en développement."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Vérifie si l'environnement est en production."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance des paramètres (singleton via cache)."""
    return Settings()


settings = get_settings()
