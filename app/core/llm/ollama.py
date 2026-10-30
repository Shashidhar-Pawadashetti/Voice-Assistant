"""Local Ollama client adapter for schema-constrained LLM inference."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.core.exceptions import LLMModelError, LLMTimeoutError, LLMUnavailableError
from app.core.llm.interface import LanguageModel


logger = logging.getLogger(__name__)


class OllamaAdapter(LanguageModel):
    """Adapter for interacting with local Ollama service.

    Non-negotiable constraints:
    - Never expose Ollama publicly (internal service only).
    - Offload any CPU-bound parsing/operations outside the event loop.
    - Explicit timeout and bounded retries.
    - JSON Schema constrained generation.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_id: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_id = model_id or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.OLLAMA_MAX_RETRIES

        # Async HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout, connect=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()

    async def generate_structured(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON adhering to the provided JSON Schema."""
        effective_timeout = timeout or self.timeout
        payload: Dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 512,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if schema:
            payload["format"] = schema

        retrier = AsyncRetrying(
            stop=stop_after_attempt(self.max_retries + 1),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=2.0),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, LLMTimeoutError)),
            reraise=True,
        )

        last_error = None
        start_time = asyncio.get_event_loop().time()

        try:
            async for attempt in retrier:
                with attempt:
                    try:
                        response = await self._client.post(
                            "/api/generate",
                            json=payload,
                            timeout=effective_timeout,
                        )
                        if response.is_error:
                            if response.status_code == 404:
                                raise LLMUnavailableError(
                                    f"Model '{self.model_id}' not found on Ollama server. Pull it first."
                                )
                            raise LLMModelError(f"Ollama returned HTTP error: {response.status_code}")
                    except (LLMUnavailableError, LLMModelError):
                        raise
                    except httpx.TimeoutException as exc:
                        logger.warning(
                            "Ollama request timed out (attempt %d/%d)",
                            attempt.retry_state.attempt_number,
                            self.max_retries + 1,
                        )
                        raise LLMTimeoutError(f"Ollama request timed out after {effective_timeout}s") from exc
                    except httpx.ConnectError as exc:
                        logger.warning(
                            "Failed to connect to Ollama at %s (attempt %d/%d)",
                            self.base_url,
                            attempt.retry_state.attempt_number,
                            self.max_retries + 1,
                        )
                        raise LLMUnavailableError(f"Could not connect to Ollama at {self.base_url}") from exc

            result_data = response.json()
            raw_response = result_data.get("response") or ""
            if not raw_response.strip() and result_data.get("thinking"):
                raw_response = result_data["thinking"]

            # Parse JSON outside the asyncio event loop using asyncio.to_thread
            parsed_json = await asyncio.to_thread(self._safe_json_parse, raw_response)
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0

            logger.info(
                "Structured extraction generated successfully",
                extra={
                    "model": self.model_id,
                    "duration_ms": round(duration_ms, 2),
                    "total_duration_ns": result_data.get("total_duration"),
                },
            )
            return parsed_json

        except (LLMTimeoutError, LLMUnavailableError, LLMModelError):
            raise
        except Exception as exc:
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
            logger.error("Unexpected error in Ollama generation: %s", exc.__class__.__name__)
            raise LLMModelError(f"LLM generation failed: {exc.__class__.__name__}") from exc

    @staticmethod
    def _safe_json_parse(raw_text: str) -> Dict[str, Any]:
        """Safely parse JSON response, stripping markdown code fences or think tags if present."""
        text = raw_text.strip()
        if "</think>" in text:
            after_think = text.split("</think>")[-1].strip()
            if after_think and "{" in after_think:
                text = after_think
            else:
                text = text.replace("<think>", "").replace("</think>", "").strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # If extra text surrounds JSON, find outer braces
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
            text = text[start_idx : end_idx + 1]

        try:
            return json.loads(text)
        except json.JSONDecodeError as err:
            logger.warning("Failed to parse LLM response as JSON: %s", err)
            raise LLMModelError(f"LLM returned malformed JSON: {err.msg}") from err

    async def check_health(self) -> tuple[bool, Optional[str], float]:
        """Check whether Ollama server is reachable and configured model is installed."""
        start_time = asyncio.get_event_loop().time()
        try:
            async with asyncio.timeout(3.0):
                resp = await self._client.get("/api/tags")
                if resp.status_code != 200:
                    latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
                    return False, f"Ollama HTTP {resp.status_code}", round(latency_ms, 2)

                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]

                # Check if configured model is in available models
                model_found = any(self.model_id in m or m.startswith(self.model_id) for m in models)
                latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0

                if not model_found:
                    return False, f"Model '{self.model_id}' not loaded in Ollama", round(latency_ms, 2)

                return True, None, round(latency_ms, 2)
        except asyncio.TimeoutError:
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
            return False, "Ollama health check timed out", round(latency_ms, 2)
        except Exception as exc:
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000.0
            return False, f"Ollama unreachable: {exc.__class__.__name__}", round(latency_ms, 2)
