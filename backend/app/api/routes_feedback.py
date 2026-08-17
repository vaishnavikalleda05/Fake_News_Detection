"""Feedback endpoints for completed analyses."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from backend.app.database.connection import mongodb
from backend.app.database.repositories import (
    analysis_repository,
    feedback_repository,
)
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
    """Save user feedback for an existing analysis."""

    if not mongodb.connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is currently unavailable.",
        )

    try:
        # Make sure the analysis actually exists.
        analysis = await analysis_repository.get_by_id(
            payload.analysis_id
        )

        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Analysis '{payload.analysis_id}' "
                    "was not found."
                ),
            )

        feedback_document = {
            "analysis_id": payload.analysis_id,
            "user_id": payload.user_id,
            "helpful": payload.helpful,
            "comment": payload.comment,
            "created_at": datetime.now(
                timezone.utc
            ),
        }

        saved = await feedback_repository.create(
            feedback_document
        )

        if not saved:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Feedback could not be saved.",
            )

        return FeedbackResponse(
            success=True,
            analysis_id=payload.analysis_id,
            helpful=payload.helpful,
            message="Feedback submitted successfully.",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback.",
        ) from exc


@router.get(
    "/{analysis_id}",
    summary="Get feedback for an analysis",
)
async def get_feedback(
    analysis_id: str,
) -> dict:
    """Return feedback associated with an analysis."""

    if not mongodb.connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is currently unavailable.",
        )

    feedback = await feedback_repository.get_by_analysis(
        analysis_id
    )

    return {
        "analysis_id": analysis_id,
        "count": len(feedback),
        "feedback": feedback,
    }