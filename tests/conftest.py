"""Pytest configuration and common fixtures."""

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional
import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment variables before importing app
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:11434"
os.environ["OLLAMA_MODEL"] = "qwen3:4b"

from app.config import Settings, get_settings
from app.core.llm.interface import LanguageModel
from app.main import create_app
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Clear lru_cache for settings between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def test_engine():
    """Create in-memory SQLite async test engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Async test client for FastAPI application."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.fixture
def kannada_fixtures() -> list[dict]:
    """Load Kannada test fixtures."""
    fixtures_path = Path(__file__).parent / "fixtures" / "kannada_fixtures.json"
    with open(fixtures_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["fixtures"]


class MockLanguageModel(LanguageModel):
    """Configurable mock LLM adapter for testing extraction logic and edge cases."""

    def __init__(
        self,
        default_response: Optional[Dict[str, Any]] = None,
        exception_to_raise: Optional[Exception] = None,
        responses_sequence: Optional[list[Dict[str, Any]]] = None,
    ):
        self.default_response = default_response or {
            "intent": "FIND_SCHEMES",
            "entities": [],
            "correction_target": None,
            "unresolved_phrases": [],
            "assistant_language": "kn",
        }
        self.exception_to_raise = exception_to_raise
        self.responses_sequence = list(responses_sequence) if responses_sequence else None
        self.call_count = 0
        self.last_prompt = None
        self.last_schema = None

    async def generate_structured(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_schema = schema

        if self.exception_to_raise:
            raise self.exception_to_raise

        if self.responses_sequence:
            idx = min(self.call_count - 1, len(self.responses_sequence) - 1)
            return self.responses_sequence[idx]

        return self.default_response

    async def check_health(self) -> tuple[bool, Optional[str], float]:
        if self.exception_to_raise:
            return False, str(self.exception_to_raise), 5.0
        return True, None, 2.5
