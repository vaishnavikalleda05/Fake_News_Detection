"""Application configuration settings using Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def find_project_root() -> Path:
    """Locate the repository root directory."""
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / "outputs").exists() and (parent / "src").exists():
            return parent
    return Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Fake News Detection API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Model path (relative to project root or absolute)
    MODEL_PATH: str = "outputs/pipeline.joblib"
    
    # CORS Origins for frontend integration
    CORS_ORIGINS: list[str] | str = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False

    # Evidence Retrieval & Fact-Checking Provider Keys (Optional)
    GOOGLE_FACTCHECK_API_KEY: str | None = None
    TAVILY_API_KEY: str | None = None
    SERPAPI_API_KEY: str | None = None
    BING_SEARCH_API_KEY: str | None = None

    # Evidence & Claim Extraction Limits
    EVIDENCE_TIMEOUT_SECONDS: float = 5.0
    MAX_CLAIMS_PER_ANALYSIS: int = 5
    MAX_EVIDENCE_PER_CLAIM: int = 5
    WIKIPEDIA_USER_AGENT: str = "FakeNewsDetectionFactChecker/1.0 (hackathon-project@example.com)"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def resolve_model_path(self) -> Path:
        """Resolve model path to an absolute path."""
        path = Path(self.MODEL_PATH)
        if path.is_absolute():
            return path
        return find_project_root() / path


settings = Settings()