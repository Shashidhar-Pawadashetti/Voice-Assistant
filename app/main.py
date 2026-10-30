"""FastAPI application entry point with lifespan, middleware, and standard error handling."""

import asyncio
import logging
import sys
import time
import uuid

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.core.exceptions import KrishiMitraError
from app.database import dispose_engine, get_engine
from app.logging import redact_sensitive_value, setup_logging
from app.schemas.error import APIErrorResponse, ErrorDetail


logger = logging.getLogger("krishi.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management."""
    settings = get_settings()
    setup_logging(level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info("Initializing Krishi Mitra backend in '%s' environment", settings.APP_ENV)

    # Initialize database engine
    get_engine()

    yield

    logger.info("Shutting down Krishi Mitra backend")
    await dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    settings = get_settings()

    is_production = settings.APP_ENV == "production"
    hide_docs = is_production and not getattr(settings, "ENABLE_PUBLIC_DOCS", False)

    app = FastAPI(
        title="Krishi Mitra AI Backend",
        description="Kannada voice-first agricultural scheme assistant backend",
        version="0.1.0",
        docs_url=None if hide_docs else "/docs",
        redoc_url=None,
        openapi_url=None if hide_docs else "/openapi.json",
        lifespan=lifespan,
    )

    # Host Validation Middleware
    if settings.allowed_hosts_list and "*" not in settings.allowed_hosts_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Request Size and Security Headers Middleware
    @app.middleware("http")
    async def request_correlation_and_logging_middleware(request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id

        # Enforce Request Size Limits (DoS prevention)
        is_voice_route = "voice" in request.url.path or "turns" in request.url.path
        max_bytes = settings.AUDIO_MAX_BYTES if is_voice_route else 2 * 1024 * 1024

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                cl_int = int(content_length)
                if cl_int > max_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body exceeds maximum allowed size of {max_bytes} bytes.",
                                "retryable": False,
                                "request_id": request_id,
                            }
                        },
                    )
            except ValueError:
                pass

        start_time = time.monotonic()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.monotonic() - start_time) * 1000.0, 2)
            status_code = response.status_code if response else 500

            # Attach correlation ID and OWASP recommended security headers
            if response:
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["X-Frame-Options"] = "DENY"
                response.headers["X-XSS-Protection"] = "1; mode=block"
                response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                response.headers["Content-Security-Policy"] = "default-src 'self'"
                if settings.APP_ENV == "production":
                    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            # Safe access log: never logs user input, transcripts, audio, or tokens
            logger.info(
                "%s %s -> %d (%.2f ms)",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "route": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )

    # Global Exception Handlers conforming to 09_API_CONTRACT.md
    @app.exception_handler(KrishiMitraError)
    async def krishi_exception_handler(request: Request, exc: KrishiMitraError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        error_resp = APIErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
                request_id=request_id,
                details=redact_sensitive_value("details", exc.details),
            )
        )
        return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Sanitize validation errors to avoid leaking user input
        sanitized_errors = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            sanitized_errors.append(f"{loc}: {err.get('msg', 'invalid value')}")

        error_resp = APIErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request payload failed validation schema.",
                retryable=False,
                request_id=request_id,
                details={"errors": sanitized_errors},
            )
        )
        return JSONResponse(status_code=422, content=error_resp.model_dump())

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        error_resp = APIErrorResponse(
            error=ErrorDetail(
                code="HTTP_ERROR",
                message=str(exc.detail),
                retryable=exc.status_code >= 500,
                request_id=request_id,
                details={"status_code": exc.status_code},
            )
        )
        return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump())

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            "Unhandled server exception: %s",
            exc.__class__.__name__,
            exc_info=True,
            extra={"request_id": request_id},
        )
        error_resp = APIErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal error occurred. Please retry later.",
                retryable=True,
                request_id=request_id,
                details={},
            )
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_resp.model_dump())

    # Mount health routers at root as well as under /api/v1
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
