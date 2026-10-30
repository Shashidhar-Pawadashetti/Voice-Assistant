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
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origins",
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")

    # Audio & Resilience (M1+ configuration)
    AUDIO_TEMP_DIR: str = Field(default="./.runtime/audio", description="Directory for temporary audio")
    AUDIO_MAX_BYTES: int = Field(default=15728640, description="Maximum audio upload bytes (15 MB)")
    AUDIO_MAX_SECONDS: int = Field(default=60, description="Maximum audio duration in seconds")
    AUDIO_RESPONSE_TTL_SECONDS: int = Field(default=600, description="TTL for ephemeral response audio (10 min)")
    FFMPEG_BINARY_PATH: str | None = Field(default=None, description="Path to ffmpeg executable if not on system PATH")

    # ASR (M1.1)
    ASR_PROVIDER: str = Field(default="indic_conformer", description="ASR provider: indic_conformer, mock")
    ASR_SERVICE_URL: str = Field(default="http://127.0.0.1:8001", description="IndicConformer service endpoint")
    ASR_TIMEOUT_SECONDS: float = Field(default=15.0, description="ASR inference timeout in seconds")
    ASR_MODEL_VERSION: str = Field(default="ai4bharat/indicconformer_asr_kn_v1", description="IndicConformer model version identifier")

    # TTS (M1.2)
    TTS_PROVIDER: str = Field(default="indic_tts", description="TTS provider: indic_tts, mock")
    TTS_SERVICE_URL: str = Field(default="http://127.0.0.1:8002", description="Indic-TTS service endpoint")
    TTS_TIMEOUT_SECONDS: float = Field(default=15.0, description="TTS inference timeout in seconds")
    TTS_VOICE_GENDER: str = Field(default="female", description="Voice gender: female or male")
    TTS_MODEL_VERSION: str = Field(default="ai4bharat/indic_tts_kn_v1", description="Indic-TTS checkpoint version identifier")

    # Security & Authentication (M5, M7)
    JWT_SECRET_KEY: str | None = Field(default=None, description="Secret key for signing JWTs (falls back to APP_SECRET_KEY)")
    JWT_ALGORITHM: str = Field(default="HS256", description="Cryptographic algorithm for JWT access tokens")
    ENCRYPTION_KEY: str | None = Field(default=None, description="Secret key for sensitive data encryption (falls back to APP_SECRET_KEY)")
    ENCRYPTION_KEY_PREVIOUS: str = Field(default="", description="Comma-separated previous encryption keys for rotation support")
    BLIND_INDEX_KEY: str | None = Field(default=None, description="Secret key for blind indexing phone numbers (falls back to APP_SECRET_KEY)")
    REDIS_URL: str | None = Field(default=None, description="Redis connection URL for shared rate limiting and token revocation (e.g. redis://127.0.0.1:6379/0)")
    REFRESH_TOKEN_ROTATION_GRACE_SECONDS: int = Field(default=30, description="Grace period in seconds for concurrent refresh token rotation")
    ENABLE_PUBLIC_DOCS: bool = Field(default=False, description="Explicitly enable public OpenAPI docs in production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token lifespan in minutes (short-lived)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token lifespan in days")
    AUTH_RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = Field(default=5, description="Max login attempts allowed within window")
    AUTH_RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = Field(default=60, description="Sliding window duration for login rate limiting")
    AUTH_RATE_LIMIT_REGISTER_MAX_ATTEMPTS: int = Field(default=5, description="Max registration attempts allowed within window")
    AUTH_RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = Field(default=300, description="Sliding window duration for registration rate limiting")
    AUTH_LOCKOUT_ATTEMPTS: int = Field(default=5, description="Failed attempts before locking farmer account")
    AUTH_LOCKOUT_DURATION_MINUTES: int = Field(default=15, description="Account lockout duration in minutes")
    ALLOWED_HOSTS: str = Field(default="*", description="Allowed HTTP Host header values (comma-separated)")

    # Model Concurrency & Backpressure (M7)
    MAX_CONCURRENT_ASR_JOBS: int = Field(default=4, description="Max concurrent ASR jobs before backpressure")
    MAX_CONCURRENT_LLM_JOBS: int = Field(default=4, description="Max concurrent LLM generation jobs before backpressure")
    MAX_CONCURRENT_TTS_JOBS: int = Field(default=4, description="Max concurrent TTS synthesis jobs before backpressure")

    @property
    def encryption_keys_previous_list(self) -> List[str]:
        """Return previous encryption keys for rotation fallback."""
        return [k.strip() for k in self.ENCRYPTION_KEY_PREVIOUS.split(",") if k.strip()]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Return allowed hosts as a list."""
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        # Enforce non-default secret key in staging and production
        # Properly inspect resolved APP_ENV from parsed settings or environment variable
        env = "local"
        if info and hasattr(info, "data") and "APP_ENV" in info.data:
            env = info.data["APP_ENV"]
        else:
            env = os.environ.get("APP_ENV", "local")

        if env in ("production", "staging") and ("insecure" in v or "dev" in v or len(v) < 32):
            raise ValueError(f"APP_SECRET_KEY must be at least 32 characters and not use defaults in {env}")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
