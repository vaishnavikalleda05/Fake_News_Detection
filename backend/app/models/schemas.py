"""API Request and Response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator

SourceType = Literal["fact_check", "official", "news", "research", "encyclopedia", "other"]
ClaimStatus = Literal["SUPPORTED", "CONTRADICTED", "INSUFFICIENT"]
FinalDecisionType = Literal["FAKE", "REAL"]


class MLAnalyzeRequest(BaseModel):
    """Input payload for ML style prediction."""

    headline: str | None = Field(
        default=None,
        description="The headline or title of the news article.",
        examples=["Breaking: Landmark climate accord signed by global leaders"],
    )
    article_text: str | None = Field(
        default=None,
        description="The main body or excerpt of the news article.",
        examples=[
            "WASHINGTON - Officials from over forty nations convened today to finalize "
            "the comprehensive international energy framework."
        ],
    )

    @model_validator(mode="after")
    def validate_content_presence(self) -> MLAnalyzeRequest:
        has_headline = bool(self.headline and self.headline.strip())
        has_article = bool(self.article_text and self.article_text.strip())
        if not (has_headline or has_article):
            raise ValueError(
                "At least one of 'headline' or 'article_text' must contain meaningful non-empty text."
            )
        return self


class MLAnalyzeResponse(BaseModel):
    """Output prediction and metadata for ML analysis."""

    prediction: str = Field(
        ...,
        description="Classification decision: 'FAKE' or 'REAL'.",
        examples=["REAL"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for the predicted label (0.0 to 1.0).",
        examples=[0.954],
    )
    prob_fake: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw model probability of the text belonging to the FAKE class.",
        examples=[0.046],
    )
    model: str = Field(
        default="TF-IDF + Logistic Regression",
        description="Name of the underlying ML architecture.",
        examples=["TF-IDF + Logistic Regression"],
    )
    char_count: int = Field(
        ...,
        ge=0,
        description="Total character count of the combined input analyzed.",
        examples=[180],
    )
    word_count: int = Field(
        ...,
        ge=0,
        description="Total word count of the combined input analyzed.",
        examples=[24],
    )
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of the analysis.",
    )

class URLAnalysisRequest(BaseModel):
    """Request to analyze an article from a URL."""

    url: str = Field(
        ...,
        min_length=10,
        description="Public article URL to analyze.",
    )
    
class ClaimItem(BaseModel):
    """Single extracted factual claim."""

    claim_id: str = Field(..., description="Unique identifier for the claim (e.g., claim_1).")
    claim_text: str = Field(..., description="Verifiable factual statement extracted from text.")
    importance_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Relative significance/importance of this claim in the article.",
    )


class EvidenceItem(BaseModel):
    """Evidence item retrieved from a reputable external source."""

    title: str = Field(..., description="Title of the source article or document.")
    source_name: str = Field(..., description="Name of the publisher or database source.")
    url: str = Field(..., description="Verifiable external URL for the citation.")
    snippet: str = Field(..., description="Relevant text excerpt or summary.")
    source_type: str = Field(
        default="news",
        description="Categorized source type (fact_check, official, news, research, encyclopedia, other).",
    )
    publication_date: str | None = Field(
        default=None,
        description="Publication date if provided by the source.",
    )
    retrieval_timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp when this evidence was retrieved.",
    )
    relevance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Calculated relevance score between claim and evidence snippet (0.0 to 1.0).",
    )
    source_quality_score: int = Field(
        default=75,
        ge=0,
        le=100,
        description="Transparent source quality score (0-100) based on domain credibility and type.",
    )
    stance: str = Field(
        default="NEUTRAL",
        description="Assessed evidence stance relative to claim: 'SUPPORTS', 'CONTRADICTS', or 'NEUTRAL'.",
    )
    provider: str = Field(..., description="Provider module that retrieved the evidence.")


class ClaimAnalysisRequest(BaseModel):
    """Input payload for claim extraction and multi-source evidence retrieval."""

    headline: str | None = Field(
        default=None,
        description="Headline or title of the news article.",
    )
    article_text: str | None = Field(
        default=None,
        description="Article body or narrative text.",
    )
    max_claims: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional limit on maximum claims to extract (defaults to server config).",
    )

    @model_validator(mode="after")
    def validate_content_presence(self) -> ClaimAnalysisRequest:
        has_headline = bool(self.headline and self.headline.strip())
        has_article = bool(self.article_text and self.article_text.strip())
        if not (has_headline or has_article):
            raise ValueError(
                "At least one of 'headline' or 'article_text' must contain meaningful non-empty text."
            )
        return self


class ClaimAnalysisResponse(BaseModel):
    """Result payload containing extracted claims and mapped evidence candidates."""

    claims: list[ClaimItem] = Field(
        default_factory=list,
        description="List of extracted factual claims.",
    )
    evidence: dict[str, list[EvidenceItem]] = Field(
        default_factory=dict,
        description="Map of claim_id to a list of retrieved evidence candidate items.",
    )
    claims_count: int = Field(..., ge=0, description="Total number of claims extracted.")
    total_evidence_count: int = Field(..., ge=0, description="Total number of evidence citations found across all claims.")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of retrieval completion.",
    )


# --- Milestone 3 Complete End-to-End Analysis Models ---

class ClaimVerificationDetail(BaseModel):
    """Detailed verification verdict for a single factual claim."""

    status: ClaimStatus = Field(
        ...,
        description="Claim verification state: 'SUPPORTED', 'CONTRADICTED', or 'INSUFFICIENT'.",
        examples=["SUPPORTED"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the verification assessment (0.0 to 1.0).",
        examples=[0.88],
    )
    reason: str = Field(
        ...,
        description="Summary explanation of the verification finding.",
        examples=["Corroborated by official reporting from Reuters and NASA."],
    )
    support_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregated support strength across independent sources.",
    )
    contradiction_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregated contradiction strength across independent sources.",
    )
    independent_sources: int = Field(
        default=0,
        ge=0,
        description="Number of unique, independent domains corroborating or refuting.",
    )


class VerifiedClaimItem(BaseModel):
    """Claim with attached verification outcome and associated evidence citations."""

    claim_id: str = Field(..., description="Unique identifier for the claim.")
    claim_text: str = Field(..., description="The factual statement.")
    importance_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Relative significance of this claim.",
    )
    verification: ClaimVerificationDetail = Field(
        ...,
        description="Verification assessment for this claim.",
    )
    evidence: list[EvidenceItem] = Field(
        default_factory=list,
        description="Retrieved and scored evidence citations for this claim.",
    )


class AnalysisInput(BaseModel):
    """Input parameters echoed in analysis results."""

    headline: str | None = None
    article_text: str | None = None


class MLAnalysisSummary(BaseModel):
    """Summary of ML style classification."""

    prediction: str = Field(..., description="'FAKE' or 'REAL'")
    confidence: float = Field(..., ge=0.0, le=1.0)
    prob_fake: float = Field(..., ge=0.0, le=1.0)
    model: str = Field(default="TF-IDF + Logistic Regression")


class FinalResult(BaseModel):
    """Final overarching decision produced by the Decision Engine."""

    decision: FinalDecisionType = Field(
        ...,
        description="Final user-facing classification: 'FAKE' or 'REAL'.",
        examples=["FAKE"],
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall decision confidence score (0.0 to 1.0).",
        examples=[0.93],
    )


class DecisionFactors(BaseModel):
    """Transparent weights and metrics feeding into the final decision."""

    ml_signal: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="ML model probability aligned to real (0=fake style, 1=real style).",
    )
    evidence_strength: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall quality and completeness of external evidence.",
    )
    supporting_claims: int = Field(default=0, ge=0)
    contradicted_claims: int = Field(default=0, ge=0)
    insufficient_claims: int = Field(default=0, ge=0)
    claim_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    claim_contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)


class CompleteAnalysisRequest(BaseModel):
    """Complete Fact-Check Analysis request payload."""

    headline: str | None = Field(
        default=None,
        description="Headline or title of the news article.",
        examples=["Breaking: Scientists discover liquid water on Mars"],
    )
    article_text: str | None = Field(
        default=None,
        description="Article body text.",
        examples=["NASA researchers announced the findings at a press briefing on Thursday."],
    )
    max_claims: int | None = Field(
        default=None,
        ge=1,
        le=10,
        description="Optional limit on maximum claims to extract.",
    )

    @model_validator(mode="after")
    def validate_content_presence(self) -> CompleteAnalysisRequest:
        has_headline = bool(self.headline and self.headline.strip())
        has_article = bool(self.article_text and self.article_text.strip())
        if not (has_headline or has_article):
            raise ValueError(
                "At least one of 'headline' or 'article_text' must contain meaningful non-empty text."
            )
        return self


class CompleteAnalysisResponse(BaseModel):
    """Full fact-checking report combining ML, claim extraction, evidence, and decision engine."""

    analysis_id: str = Field(
        default_factory=lambda: f"analysis_{uuid.uuid4().hex[:12]}",
        description="Unique identifier for this analysis run.",
    )
    input: AnalysisInput = Field(..., description="Echoed input parameters.")
    ml_analysis: MLAnalysisSummary = Field(..., description="Baseline ML stylistic classification.")
    claims: list[VerifiedClaimItem] = Field(
        default_factory=list,
        description="List of verified claims with attached evidence citations.",
    )
    final_result: FinalResult = Field(
        ...,
        description="Definitive decision: 'FAKE' or 'REAL' with confidence.",
    )
    decision_factors: DecisionFactors = Field(
        ...,
        description="Detailed quantitative breakdown of decision factors.",
    )
    explanation: str = Field(
        ...,
        description="Synthesized natural-language explanation grounded in data.",
    )
    analyzed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of analysis completion.",
    )


class HealthResponse(BaseModel):
    """Service health and readiness response."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., examples=["Fake News Detection API"])
    ml_model_loaded: bool = Field(..., examples=[True])
    version: str = Field(..., examples=["1.0.0"])
    model_path: str | None = Field(
        default=None,
        examples=["outputs/pipeline.joblib"],
    )
    database: str = Field(
        default="unavailable",
        examples=["unavailable"],
        description="Database status (deprecated - database removed).",
    )

class ErrorResponse(BaseModel):
    """Standardized error payload."""

    detail: str = Field(..., description="Human-readable description of the error.")
    error_code: str | None = Field(default=None, description="Optional application error code.")    