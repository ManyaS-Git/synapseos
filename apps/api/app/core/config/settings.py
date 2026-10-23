"""Centralized configuration system for SynapseOS.

Loads settings from environment variables and .env files.
Validates all required configuration at startup.
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class AppSettings(BaseSettings):
    """Application-level settings."""

    data_dir: str = Field(default=DATA_DIR, description="Directory for persistent data")

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
    enable_docs_in_production: bool = Field(default=False, description="Enable /docs and /redoc in production")
    storage_mode: str = Field(
        default="auto",
        description="Storage mode: 'auto' (detect services, fallback to local), 'local_embedded', or 'distributed'",
    )

    # CORS
    cors_origins: list[str] | str = Field(
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

    # LLM & Providers
    llm_default_provider: str = Field(default="nebius", description="Default LLM provider: nebius, local, openai, mock")
    llm_provider: str = Field(default="nebius", description="Active LLM provider: nebius, local, openai, mock")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="llama3.2", description="Default Ollama model")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # Nebius Token Factory / NVIDIA Nemotron Settings
    nebius_api_key: str = Field(default="", description="Nebius Token Factory API key")
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.nebius.com/v1",
        description="Nebius Token Factory OpenAI-compatible API base URL",
    )
    nebius_model: str = Field(
        default="nvidia/Llama-3.1-Nemotron-70B-Instruct-HF",
        description="NVIDIA Nemotron model on Nebius Token Factory",
    )
    nebius_timeout_seconds: float = Field(
        default=60.0,
        description="Timeout for Nebius inference requests in seconds",
    )

    # Privacy and Data Routing
    privacy_mode: str = Field(
        default="hybrid",
        description="Privacy boundary: local_only, hybrid, cloud_allowed",
    )

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

    @field_validator("cors_origins")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> list[str]:
        """Support comma-separated strings or JSON lists for CORS origins."""
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v_str.split(",") if i.strip()]
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip()]
        return ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_production_security(self) -> AppSettings:
        """Validate critical security invariants when running in production."""
        if self.app_env == Environment.PRODUCTION:
            if self.app_debug:
                raise ValueError("app_debug must be set to False in production mode.")

            insecure_app_secrets = {
                "change-me-in-production",
                "change-me-to-a-random-secret-key",
                "secret",
                "admin",
                "synapseos",
                "password",
            }
            if self.app_secret_key in insecure_app_secrets or len(self.app_secret_key) < 16:
                raise ValueError(
                    "In production, app_secret_key must not use a default placeholder and must be at least 16 characters long."
                )

            insecure_jwt_secrets = {
                "change-me-to-jwt-secret",
                "change-me-to-a-random-jwt-secret",
                "secret",
                "admin",
                "synapseos",
                "password",
            }
            if self.jwt_secret_key in insecure_jwt_secrets or len(self.jwt_secret_key) < 16:
                raise ValueError(
                    "In production, jwt_secret_key must not use a default placeholder and must be at least 16 characters long."
                )

            if "*" in self.cors_origins:
                raise ValueError(
                    "In production, cors_origins must not contain wildcard '*' when allow_credentials is True."
                )

        return self


    @property
    def database_url(self) -> str:
        """Async database connection URL."""
        if self.storage_mode == "local_embedded":
            local_dir = self.data_dir
            os.makedirs(local_dir, exist_ok=True)
            local_db_path = os.path.join(local_dir, "synapseos_local.db")
            return f"sqlite+aiosqlite:///{local_db_path}"
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchronous database connection URL (for Alembic)."""
        if self.storage_mode == "local_embedded":
            local_dir = self.data_dir
            os.makedirs(local_dir, exist_ok=True)
            local_db_path = os.path.join(local_dir, "synapseos_local.db")
            return f"sqlite:///{local_db_path}"
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
