"""Feedback endpoints for completed analyses."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.app.models.schemas import (
    FeedbackRequest,
    FeedbackResponse,
)

router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
)


@router.post(
    "",
    response_model=FeedbackResponse,
    summary="Submit analysis feedback",
)
async def submit_feedback(
    payload: FeedbackRequest,
) -> FeedbackResponse:
    """Feedback feature is not available (database removed)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Feedback feature is not available. Database persistence has been removed.",
    )


@router.get(
    "/{analysis_id}",
    summary="Get feedback for an analysis",
)
async def get_feedback(
    analysis_id: str,
) -> dict:
    """Feedback feature is not available (database removed)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Feedback feature is not available. Database persistence has been removed.",
    )