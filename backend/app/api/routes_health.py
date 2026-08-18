"""Health and readiness check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.config import settings
from backend.app.models.schemas import HealthResponse
from backend.app.services.ml_service import ml_service

router = APIRouter(tags=["Health & Status"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health and model readiness",
    description=(
        "Returns API status, service name, version, ML model readiness, "
        "and model path."
    ),
)
async def check_health() -> HealthResponse:
    """Return service health and ML readiness."""

    return HealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        ml_model_loaded=ml_service.is_loaded,
        version=settings.VERSION,
        model_path=str(ml_service.model_path),
    )