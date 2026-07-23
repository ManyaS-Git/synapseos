"""Centralized configuration system for SynapseOS.

Loads settings from environment variables and .env files.
Validates all required configuration at startup.
"""

from enum import Enum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class AppSettings(BaseSettings):
    """Application-level settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="SynapseOS", description="Application name")
    app_env: Environment = Field(default=Environment.DEVELOPMENT, description="Current environment")
    app_debug: bool = Field(default=True, description="Enable debug mode")
    app_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for signing",
    )
    app_log_level: str = Field(default="INFO", description="Logging level")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins",
    )

    # PostgreSQL
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="synapseos", description="PostgreSQL database name")
    postgres_user: str = Field(default="synapseos", description="PostgreSQL user")
    postgres_password: str = Field(default="synapseos_dev_password", description="PostgreSQL password")

    # Redis
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: str = Field(default="", description="Redis password")

    # Neo4j
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j Bolt URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="synapseos_dev_password", description="Neo4j password")
    neo4j_database: str = Field(default="synapseos", description="Neo4j database name")

    # Qdrant
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant REST port")
    qdrant_grpc_port: int = Field(default=6334, description="Qdrant gRPC port")
    qdrant_collection: str = Field(default="synapseos", description="Qdrant collection name")

    # LLM / Ollama
    llm_default_provider: str = Field(default="local", description="Default LLM provider")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="llama3.2", description="Default Ollama model")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # JWT
    jwt_secret_key: str = Field(default="change-me-to-jwt-secret", description="JWT signing key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_minutes: int = Field(default=30, description="Access token expiry in minutes")
    jwt_refresh_token_days: int = Field(default=7, description="Refresh token expiry in days")
    jwt_cookie_name: str = Field(default="synapseos_session", description="JWT cookie name")
    jwt_cookie_domain: str | None = Field(default=None, description="JWT cookie domain")

    # Logging
    log_format: str = Field(default="console", description="Log format: console or json")
    log_file: str = Field(default="logs/synapseos.log", description="Log file path")
    log_max_bytes: int = Field(default=10_485_760, description="Max log file size in bytes")
    log_backup_count: int = Field(default=5, description="Number of log backup files")

    @field_validator("postgres_password", "neo4j_password")
    @classmethod
    def warn_default_password(cls, v: str, info: object) -> str:  # noqa: ARG001
        """Warn if default passwords are used in production."""
        return v

    @property
    def database_url(self) -> str:
        """Async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchronous PostgreSQL connection URL (for Alembic)."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.app_env == Environment.TESTING


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings.

    The settings are loaded once and cached for the lifetime of the process.
    Use this function to access settings throughout the application.

    Returns:
        Cached AppSettings instance.
    """
    return AppSettings()


# Module-level convenience alias
settings = get_settings()
