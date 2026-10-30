"""Unit tests for configuration loading and validation."""

import os
import pytest
from app.config import Settings


def test_default_settings():
    """Verify safe default configuration."""
    settings = Settings()
    assert settings.APP_ENV in ("local", "test")
    assert settings.APP_PORT == 8000
    assert settings.OLLAMA_MODEL == "qwen3:4b"
    assert settings.OLLAMA_TIMEOUT_SECONDS == 30.0
    assert settings.OLLAMA_MAX_RETRIES == 1
    assert "http://localhost:3000" in settings.cors_origins_list


def test_cors_origins_list():
    """Verify CORS comma-separated string parsing."""
    settings = Settings(CORS_ORIGINS="https://app.krishimitra.in, https://beta.krishimitra.in")
    assert settings.cors_origins_list == ["https://app.krishimitra.in", "https://beta.krishimitra.in"]


def test_production_secret_key_validation():
    """Verify that insecure default keys are rejected in production."""
    with pytest.raises(ValueError, match="APP_SECRET_KEY"):
        # Simulate production environment
        os.environ["APP_ENV"] = "production"
        try:
            Settings(
                APP_SECRET_KEY="dev-insecure-secret-key-change-in-production-min32chars",
            )
        finally:
            os.environ["APP_ENV"] = "test"
