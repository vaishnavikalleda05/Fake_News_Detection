"""Analysis history endpoints backed by MongoDB."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from backend.app.utils.logger import logger
from backend.app.database.connection import mongodb
from backend.app.database.repositories import (
    analysis_repository,
    claim_repository,
    evidence_repository,
)


router = APIRouter(
    prefix="/history",
    tags=["Analysis History"],
)


@router.get(
    "",
    summary="Get analysis history",
    description="Returns recent analyses for a user.",
)
async def get_analysis_history(
    user_id: str = Query(
        default="anonymous",
        min_length=1,
        max_length=100,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
) -> dict:
    """Return recent analysis history."""

    if not mongodb.connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is currently unavailable.",
        )

    try:
        analyses = await analysis_repository.get_history(
            user_id=user_id,
            limit=limit,
        )

        return {
            "user_id": user_id,
            "count": len(analyses),
            "analyses": analyses,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis history.",
        ) from exc


@router.get(
    "/{analysis_id}",
    summary="Get analysis details",
    description="Returns a complete saved analysis by analysis ID.",
)
async def get_analysis_detail(
    analysis_id: str,
) -> dict:
    """Return a saved analysis with its claims and evidence."""

    if not mongodb.connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is currently unavailable.",
        )

    try:
        analysis = await analysis_repository.get_by_id(
            analysis_id
        )

        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis '{analysis_id}' was not found.",
            )

        claims = await claim_repository.get_by_analysis(
            analysis_id
        )

        evidence = await evidence_repository.get_by_analysis(
            analysis_id
        )

        analysis["claims"] = claims
        analysis["evidence"] = evidence

        return analysis

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "Failed to retrieve analysis '%s': %s",
            analysis_id,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis.",
        ) from exc




@router.delete(
    "/{analysis_id}",
    summary="Delete an analysis",
    description=(
        "Deletes an analysis and all claims and evidence "
        "associated with that analysis."
    ),
)
async def delete_analysis(
    analysis_id: str,
) -> dict:
    """Delete an analysis and its related claims and evidence."""

    if not mongodb.connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is currently unavailable.",
        )

    try:
        # Check whether the analysis exists first.
        analysis = await analysis_repository.get_by_id(
            analysis_id
        )

        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis '{analysis_id}' was not found.",
            )

        # Delete the main analysis document.
        deleted = await analysis_repository.delete(
            analysis_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis '{analysis_id}' was not found.",
            )

        # Delete all claims belonging to this analysis.
        await claim_repository.delete_by_analysis(
            analysis_id
        )

        # Delete all evidence belonging to this analysis.
        await evidence_repository.delete_by_analysis(
            analysis_id
        )

        return {
            "success": True,
            "analysis_id": analysis_id,
            "message": (
                "Analysis, claims, and evidence "
                "deleted successfully."
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete analysis.",
        ) from exc