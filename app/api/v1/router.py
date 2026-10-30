"""V1 API Router aggregation."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.extraction import router as extraction_router
from app.api.v1.voice import router as voice_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.schemes import router as schemes_router


api_v1_router = APIRouter()

# Mount health endpoints under /api/v1 as well as root
api_v1_router.include_router(health_router)
api_v1_router.include_router(extraction_router)
api_v1_router.include_router(voice_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(schemes_router)
