"""Configuration management for Krishi Mitra AI backend using Pydantic Settings."""

import os
from functools import lru_cache
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_ENV: str = Field(default="local", description="Environment: local, staging, production")
    APP_HOST: str = Field(default="0.0.0.0", description="Bind host")
    APP_PORT: int = Field(default=8000, description="Bind port")
    APP_SECRET_KEY: str = Field(
        default="dev-insecure-secret-key-change-in-production-min32chars",
        description="Secret key for signing tokens and sessions",
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://krishi_app:krishi_mitra_dev_pass@127.0.0.1:5432/krishi_mitra",
        description="SQLAlchemy database connection URI",
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=5, description="Max overflow connections")
    DATABASE_TIMEOUT_SECONDS: float = Field(default=5.0, description="Database ping timeout in seconds")

    # Ollama LLM
    OLLAMA_BASE_URL: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama server endpoint (must remain internal/private)",
    )
    OLLAMA_MODEL: str = Field(
        default="qwen3:4b",
        description="Model identifier for NLU slot/intent extraction",
    )
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=30.0, description="Timeout for LLM inference in seconds")
    OLLAMA_MAX_RETRIES: int = Field(default=1, description="Bounded retry attempts for schema validation failure")
    OLLAMA_TEMPERATURE: float = Field(default=0.1, description="Low temperature for deterministic extraction")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated allowed CORS origins",
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")

    # Audio & Resilience (M1+ configuration)
    AUDIO_TEMP_DIR: str = Field(default="./.runtime/audio", description="Directory for temporary audio")
    AUDIO_MAX_BYTES: int = Field(default=15728640, description="Maximum audio upload bytes (15 MB)")
    AUDIO_MAX_SECONDS: int = Field(default=60, description="Maximum audio duration in seconds")
    AUDIO_RESPONSE_TTL_SECONDS: int = Field(default=600, description="TTL for ephemeral response audio")

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # In production, enforce non-default secret key
        env = os.environ.get("APP_ENV", "local")
        if env == "production" and ("insecure" in v or len(v) < 32):
            raise ValueError("APP_SECRET_KEY must be at least 32 characters and not use defaults in production")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
