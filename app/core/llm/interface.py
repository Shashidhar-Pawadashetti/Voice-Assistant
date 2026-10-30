"""LanguageModel protocol definition."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class LanguageModel(Protocol):
    """Protocol for LLM inference adapters."""

    async def generate_structured(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate schema-constrained structured JSON output from LLM."""
        ...

    async def check_health(self) -> tuple[bool, Optional[str], float]:
        """Check whether the model endpoint and configured model are available.

        Returns:
            (is_available, error_message, latency_ms)
        """
        ...
