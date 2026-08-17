"""News analysis, ML prediction, Claim retrieval, and Complete Decision Engine endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status

from backend.app.models.schemas import (
    AnalysisInput,
    ClaimAnalysisRequest,
    ClaimAnalysisResponse,
    CompleteAnalysisRequest,
    CompleteAnalysisResponse,
    ErrorResponse,
    MLAnalysisSummary,
    MLAnalyzeRequest,
    MLAnalyzeResponse,
)
from backend.app.models.schemas import URLAnalysisRequest
from backend.app.services.article_url_service import article_url_service
from backend.app.services.claim_extractor import claim_extractor
from backend.app.services.claim_verification_service import (
    claim_verification_service,
)
from backend.app.services.decision_engine import decision_engine
from backend.app.services.evidence_retriever import evidence_retriever
from backend.app.services.explanation_service import explanation_service
from backend.app.services.ml_service import ml_service
from backend.app.utils.logger import logger

# MongoDB persistence
from backend.app.database.connection import mongodb
from backend.app.database.repositories import (
    analysis_repository,
    claim_repository,
    evidence_repository,
)


router = APIRouter(prefix="/analyze", tags=["News Analysis"])


def _model_to_dict(value: Any) -> dict[str, Any]:
    """
    Convert a Pydantic model to a dictionary.

    This keeps persistence compatible with the project's existing
    Pydantic schemas without hard-coding every schema field here.
    """
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    if isinstance(value, dict):
        return value.copy()

    return {}


def _safe_value(value: Any, default: Any = None) -> Any:
    """Return a value safely from a Pydantic model or dictionary."""
    if isinstance(value, dict):
        return value.get(default if False else "", default)

    return value if value is not None else default


async def _persist_analysis(
    *,
    analysis_id: str,
    payload: CompleteAnalysisRequest,
    ml_summary: MLAnalysisSummary,
    verified_claims: list[Any],
    evidence_map: dict[str, list[Any]],
    final_result: Any,
    decision_factors: Any,
    decision_reason: str,
    explanation: str,
    analyzed_at: datetime,
) -> bool:
    """
    Persist a completed analysis to MongoDB.

    Database errors are intentionally isolated from the analysis pipeline.
    A user should still receive an analysis result if MongoDB is unavailable.
    """

    if not mongodb.connected:
        logger.warning(
            "[%s] MongoDB unavailable; analysis was not persisted.",
            analysis_id,
        )
        return False

    try:
        # ---------------------------------------------------------
        # 1. Main analysis document
        # ---------------------------------------------------------

        final_result_data = _model_to_dict(final_result)

        final_decision = getattr(
            final_result,
            "decision",
            None,
        )

        final_confidence = getattr(
            final_result,
            "confidence",
            None,
        )

        # Fallback in case final_result is represented as a dictionary.
        if isinstance(final_result, dict):
            final_decision = final_result.get(
                "decision",
                final_decision,
            )
            final_confidence = final_result.get(
                "confidence",
                final_confidence,
            )

        analysis_document: dict[str, Any] = {
            "analysis_id": analysis_id,

            # Authentication/user system will be added later.
            "user_id": "anonymous",

            "headline": payload.headline,
            "article_text": payload.article_text,

            "ml_prediction": ml_summary.prediction,
            "ml_confidence": ml_summary.confidence,
            "prob_fake": ml_summary.prob_fake,
            "ml_model": ml_summary.model,

            "final_decision": final_decision,
            "final_confidence": final_confidence,

           "decision_factors": _model_to_dict(decision_factors),
            "decision_reason": decision_reason,
            "explanation": explanation,

            "total_claims": len(verified_claims),

            "evidence_count": sum(
                len(items)
                for items in evidence_map.values()
            ),

            "final_result": final_result_data,

            "created_at": analyzed_at,
        }

        await analysis_repository.create(
            analysis_document
        )

        # ---------------------------------------------------------
        # 2. Claims
        # ---------------------------------------------------------

        claim_documents: list[dict[str, Any]] = []

        for claim in verified_claims:
            claim_data = _model_to_dict(claim)

            claim_id = claim_data.get(
                "claim_id",
                getattr(claim, "claim_id", None),
            )

            claim_documents.append(
                {
                    "analysis_id": analysis_id,
                    "claim_id": claim_id,

                    # Preserve the complete verified claim object.
                    **claim_data,

                    "created_at": analyzed_at,
                }
            )

        if claim_documents:
            await claim_repository.create_many(
                claim_documents
            )

        # ---------------------------------------------------------
        # 3. Evidence
        # ---------------------------------------------------------

        evidence_documents: list[dict[str, Any]] = []

        for claim_id, evidence_items in evidence_map.items():

            for evidence in evidence_items:
                evidence_data = _model_to_dict(
                    evidence
                )

                evidence_documents.append(
                    {
                        "analysis_id": analysis_id,
                        "claim_id": claim_id,

                        # Preserve the complete evidence object.
                        **evidence_data,

                        "created_at": analyzed_at,
                    }
                )

        if evidence_documents:
            await evidence_repository.create_many(
                evidence_documents
            )

        logger.info(
            "[%s] Analysis, claims, and evidence "
            "successfully persisted to MongoDB.",
            analysis_id,
        )

        return True

    except Exception as exc:
        logger.exception(
            "[%s] MongoDB persistence failed: %s",
            analysis_id,
            exc,
        )

        # Important:
        # Database failure must never make a successful
        # fake-news analysis return HTTP 500.
        return False


# =====================================================================
# COMPLETE ANALYSIS
# =====================================================================

@router.post(
    "",
    response_model=CompleteAnalysisResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid input.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "ML Model unavailable.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Analysis failed.",
        },
    },
    summary="Complete Fake News Detection & Multi-Source Verification Analysis",
    description=(
        "Executes end-to-end fact-checking: ML stylistic risk classification, "
        "factual claim extraction, multi-source evidence retrieval, "
        "independent source scoring, claim-level stance verification, "
        "hybrid decision engine synthesis, human-readable explanation "
        "generation, and MongoDB persistence."
    ),
)
async def analyze_complete(
    payload: CompleteAnalysisRequest,
) -> CompleteAnalysisResponse:
    """Run comprehensive multi-layer fact-check analysis."""

    if not ml_service.is_loaded:
        logger.error(
            "Analysis requested but ML model is not loaded: %s",
            ml_service.load_error,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ML classification model is unavailable. "
                f"Error: {ml_service.load_error or 'Artifact missing.'}"
            ),
        )

    # Create the ID before entering try so the exception handler
    # can always safely reference it.
    analysis_id = (
        f"analysis_{uuid.uuid4().hex[:12]}"
    )

    analyzed_at = datetime.now(timezone.utc)

    try:
        logger.info(
            "[%s] Starting complete fact-check analysis...",
            analysis_id,
        )

        # =========================================================
        # 1. ML Stylistic Inference
        # =========================================================

        ml_res = ml_service.predict(
            headline=payload.headline,
            article_text=payload.article_text,
        )

        ml_summary = MLAnalysisSummary(
            prediction=ml_res["prediction"],
            confidence=ml_res["confidence"],
            prob_fake=ml_res["prob_fake"],
            model=ml_res["model"],
        )

        logger.info(
            "[%s] ML Prediction: %s (Confidence: %.2f)",
            analysis_id,
            ml_summary.prediction,
            ml_summary.confidence,
        )

        # =========================================================
        # 2. Claim Extraction
        # =========================================================

        raw_claims = claim_extractor.extract_claims(
            headline=payload.headline,
            article_text=payload.article_text,
            max_claims=payload.max_claims,
        )

        logger.info(
            "[%s] Extracted %d factual claims",
            analysis_id,
            len(raw_claims),
        )

        # =========================================================
        # 3. Evidence Retrieval
        # =========================================================

        evidence_map: dict[str, list[Any]] = {}

        if raw_claims:
            try:
                evidence_map = (
                    await evidence_retriever
                    .retrieve_evidence_for_claims(
                        raw_claims
                    )
                )

                total_ev = sum(
                    len(evs)
                    for evs in evidence_map.values()
                )

                logger.info(
                    "[%s] Retrieved %d evidence items "
                    "across %d claims",
                    analysis_id,
                    total_ev,
                    len(raw_claims),
                )

            except Exception as exc:
                logger.warning(
                    "[%s] Evidence retrieval encountered "
                    "non-fatal error: %s",
                    analysis_id,
                    exc,
                )

                evidence_map = {
                    claim.claim_id: []
                    for claim in raw_claims
                }

        # =========================================================
        # 4. Claim-Level Verification & Source Scoring
        # =========================================================

        verified_claims = (
            claim_verification_service
            .verify_all_claims(
                claims=raw_claims,
                evidence_map=evidence_map,
            )
        )

        # =========================================================
        # 5. Hybrid Decision Engine
        # =========================================================

        (
            final_result,
            decision_factors,
            decision_reason,
        ) = decision_engine.compute_decision(
            ml_prediction=ml_summary.prediction,
            ml_confidence=ml_summary.confidence,
            prob_fake=ml_summary.prob_fake,
            verified_claims=verified_claims,
        )

        logger.info(
            "[%s] Final Decision: %s "
            "(Confidence: %.2f) - Reason: %s",
            analysis_id,
            final_result.decision,
            final_result.confidence,
            decision_reason,
        )

        # =========================================================
        # 6. Explanation Generation
        # =========================================================

        explanation = (
            explanation_service.generate_explanation(
                ml_analysis=ml_summary,
                verified_claims=verified_claims,
                final_result=final_result,
                decision_factors=decision_factors,
            )
        )

        # =========================================================
        # 7. MongoDB Persistence
        # =========================================================

        persistence_success = await _persist_analysis(
            analysis_id=analysis_id,
            payload=payload,
            ml_summary=ml_summary,
            verified_claims=verified_claims,
            evidence_map=evidence_map,
            final_result=final_result,
            decision_factors=decision_factors,
            decision_reason=decision_reason,
            explanation=explanation,
            analyzed_at=analyzed_at,
        )

        if persistence_success:
            logger.info(
                "[%s] Persistence status: saved",
                analysis_id,
            )
        else:
            logger.warning(
                "[%s] Persistence status: unavailable",
                analysis_id,
            )

        # =========================================================
        # 8. Return Complete Analysis
        # =========================================================

        return CompleteAnalysisResponse(
            analysis_id=analysis_id,

            input=AnalysisInput(
                headline=payload.headline,
                article_text=payload.article_text,
            ),

            ml_analysis=ml_summary,

            claims=verified_claims,

            final_result=final_result,

            decision_factors=decision_factors,

            explanation=explanation,

            analyzed_at=analyzed_at.isoformat(),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "[%s] Unexpected error during "
            "complete analysis: %s",
            analysis_id,
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An internal error occurred while "
                "performing complete fact-check analysis."
            ),
        ) from exc


# =====================================================================
# ML ONLY
# =====================================================================

@router.post(
    "/ml-only",
    response_model=MLAnalyzeResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid or empty input text.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ErrorResponse,
            "description": "ML Model is not loaded.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Prediction failed.",
        },
    },
    summary="Classify news style using the ML model",
    description=(
        "Accepts a news headline and/or article text, "
        "preprocesses it through the custom TextCleaner and "
        "TF-IDF vectorizer, and returns a classification "
        "(FAKE or REAL) with confidence score."
    ),
)
async def analyze_ml_only(
    payload: MLAnalyzeRequest,
) -> MLAnalyzeResponse:
    """Analyze news content using the trained ML model."""

    if not ml_service.is_loaded:
        logger.error(
            "Prediction requested but ML model is not loaded: %s",
            ml_service.load_error,
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ML classification model is currently unavailable. "
                f"Error: {ml_service.load_error or 'Artifact not loaded.'}"
            ),
        )

    try:
        result = ml_service.predict(
            headline=payload.headline,
            article_text=payload.article_text,
        )

        return MLAnalyzeResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected error during ML inference: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An internal error occurred while "
                "processing the news text."
            ),
        ) from exc


# =====================================================================
# CLAIMS + EVIDENCE
# =====================================================================

@router.post(
    "/claims",
    response_model=ClaimAnalysisResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Invalid or empty input text.",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Claim extraction failed.",
        },
    },
    summary="Extract factual claims and retrieve multi-source evidence",
    description=(
        "Extracts discrete factual statements from the headline "
        "and article text, then searches multi-source evidence "
        "providers (Google Fact Check, Web Search, Wikipedia) "
        "and returns deduplicated, ranked evidence citations."
    ),
)
async def analyze_claims_and_evidence(
    payload: ClaimAnalysisRequest,
) -> ClaimAnalysisResponse:
    """Extract claims and retrieve evidence candidates."""

    try:
        claims = claim_extractor.extract_claims(
            headline=payload.headline,
            article_text=payload.article_text,
            max_claims=payload.max_claims,
        )

        if not claims:
            return ClaimAnalysisResponse(
                claims=[],
                evidence={},
                claims_count=0,
                total_evidence_count=0,
            )

        evidence_map = (
            await evidence_retriever
            .retrieve_evidence_for_claims(claims)
        )

        total_evidence = sum(
            len(items)
            for items in evidence_map.values()
        )

        return ClaimAnalysisResponse(
            claims=claims,
            evidence=evidence_map,
            claims_count=len(claims),
            total_evidence_count=total_evidence,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Error extracting claims and retrieving evidence: %s",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An error occurred while extracting claims "
                "and retrieving evidence."
            ),
        ) from exc

# =====================================================================
# ARTICLE URL ANALYSIS
# =====================================================================

@router.post(
    "/url",
    response_model=CompleteAnalysisResponse,
    summary="Analyze a news article from a URL",
    description=(
        "Fetches a public news article URL, extracts the readable "
        "article content, and sends it through the same complete "
        "fake-news detection and evidence-verification pipeline."
    ),
)
async def analyze_article_url(
    request: URLAnalysisRequest,
) -> CompleteAnalysisResponse:
    """Fetch and analyze a news article from a public URL."""

    # ---------------------------------------------------------
    # 1. Extract article content from URL
    # ---------------------------------------------------------

    article = await article_url_service.extract_article(
        request.url
    )

    # ---------------------------------------------------------
    # 2. Build the existing analysis request
    # ---------------------------------------------------------

    analysis_request = CompleteAnalysisRequest(
        headline=article["headline"],
        article_text=article["article_text"],
    )

    # ---------------------------------------------------------
    # 3. Reuse the existing complete analysis pipeline
    # ---------------------------------------------------------

    return await analyze_complete(analysis_request)