"""FastAPI Application Entrypoint for Fake News Detection API."""

from __future__ import annotations

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes_analysis import router as analysis_router
from backend.app.api.routes_feedback import router as feedback_router
from backend.app.api.routes_health import router as health_router
from backend.app.api.routes_history import router as history_router
from backend.app.api.routes_metrics import router as metrics_router
from backend.app.config import find_project_root, settings
from backend.app.database.connection import mongodb
from backend.app.services.ml_service import ml_service
from backend.app.utils.logger import logger

# Ensure project root & src are accessible for deserialization
_PROJECT_ROOT = find_project_root()
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""

    logger.info(
        "Initializing %s v%s...",
        settings.PROJECT_NAME,
        settings.VERSION,
    )

    logger.info(
        "Configured CORS origins: %s",
        settings.CORS_ORIGINS,
    )

    # ---------------------------------------------------------
    # Load ML pipeline once on startup
    # ---------------------------------------------------------
    loaded = ml_service.load_model()

    if loaded:
        logger.info(
            "[OK] ML Service successfully initialized with pipeline: %s",
            ml_service.model_path,
        )
    else:
        logger.warning(
            "[WARN] ML Service failed to load pipeline: %s",
            ml_service.load_error,
        )

    # ---------------------------------------------------------
    # Connect to MongoDB
    # ---------------------------------------------------------
    database_connected = await mongodb.connect(
        settings.MONGODB_URI,
        settings.MONGODB_DATABASE,
    )

    if database_connected:
        logger.info(
            "[OK] MongoDB connected successfully: %s",
            settings.MONGODB_DATABASE,
        )
    else:
        logger.warning(
            "[WARN] MongoDB unavailable. "
            "Application will continue without persistence."
        )

    # ---------------------------------------------------------
    # Application is ready
    # ---------------------------------------------------------
    yield

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------
    await mongodb.disconnect()

    logger.info(
        "Shutting down %s...",
        settings.PROJECT_NAME,
    )

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Production-ready FastAPI backend for Fake News Detection. "
        "Provides style/linguistic risk classification and integrates with existing ML pipelines."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom validation exception handler to ensure clean user-facing error formats
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    # Format message cleanly
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(part) for part in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{loc}: {msg}")
    
    formatted_detail = "; ".join(error_messages) or "Invalid request payload."
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, formatted_detail)
    return JSONResponse(
        status_code=422,
        content={"detail": formatted_detail, "error_code": "VALIDATION_ERROR"},
    )


# Include API Routers under /api
app.include_router(
    health_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    analysis_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    history_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    feedback_router,
    prefix=settings.API_PREFIX,
)

app.include_router(
    metrics_router,
    prefix=settings.API_PREFIX,
)
app.include_router(metrics_router, prefix="/api")

@app.get("/", tags=["Root"], include_in_schema=False)
async def root_redirect() -> dict[str, str]:
    """Root endpoint welcoming API consumers and linking to documentation."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": f"{settings.API_PREFIX}/health",
        "analysis_endpoint": f"{settings.API_PREFIX}/analyze/ml-only",
    }