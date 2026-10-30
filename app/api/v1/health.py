"""Health check endpoints conforming to 09_API_CONTRACT.md and 13_SCALABILITY_AND_OPERATIONS.md."""

from fastapi import APIRouter, Response, status
from app.database import check_database_health
from app.core.llm.ollama import OllamaAdapter
from app.schemas.health import DependencyHealth, LivenessResponse, ReadinessResponse


router = APIRouter(tags=["Health"])


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness check",
    description="Fast process liveness check. Does not execute external dependency checks.",
)
async def liveness() -> LivenessResponse:
    """Return process liveness."""
    return LivenessResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Verifies external dependencies needed to accept work without exposing credentials or internal topology.",
)
async def readiness(response: Response) -> ReadinessResponse:
    """Check health of PostgreSQL database and local Ollama model server."""
    db_ok, db_err, db_latency = await check_database_health()

    ollama = OllamaAdapter()
    try:
        ollama_ok, ollama_err, ollama_latency = await ollama.check_health()
    finally:
        await ollama.close()

    dependencies = {
        "database": DependencyHealth(
            status="UP" if db_ok else "DOWN",
            latency_ms=db_latency,
            error=db_err,
        ),
        "ollama": DependencyHealth(
            status="UP" if ollama_ok else "DOWN",
            latency_ms=ollama_latency,
            error=ollama_err,
        ),
    }

    # If the database is down, system cannot accept stateful work
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        overall_status = "degraded"
    else:
        response.status_code = status.HTTP_200_OK
        overall_status = "ok" if ollama_ok else "degraded"

    return ReadinessResponse(
        status=overall_status,
        dependencies=dependencies,
    )
