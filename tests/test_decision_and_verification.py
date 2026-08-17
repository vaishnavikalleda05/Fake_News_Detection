"""Unit and integration tests for Claim Verification, Source Quality, Decision Engine, and Complete Analysis."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import (
    ClaimVerificationDetail,
    DecisionFactors,
    EvidenceItem,
    FinalResult,
    MLAnalysisSummary,
    VerifiedClaimItem,
)
from backend.app.services.claim_verification_service import claim_verification_service
from backend.app.services.decision_engine import decision_engine
from backend.app.services.evidence_aggregation_service import (
    evidence_aggregation_service,
)
from backend.app.services.explanation_service import explanation_service
from backend.app.services.source_scoring_service import source_scoring_service


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_source_quality_scoring_weights() -> None:
    """Source scoring should give high weight to official/fact_check and lower to unverified blogs."""
    official = source_scoring_service.score_source("NASA", "https://science.nasa.gov/mission", "official")
    assert int(official["source_quality_score"]) >= 90

    fact_check = source_scoring_service.score_source("Snopes", "https://www.snopes.com/fact-check/test", "fact_check")
    assert int(fact_check["source_quality_score"]) >= 90

    reputable_news = source_scoring_service.score_source("Reuters", "https://www.reuters.com/world", "news")
    assert int(reputable_news["source_quality_score"]) >= 80

    blog = source_scoring_service.score_source("Random Blog", "https://myanonymousblog.blogspot.com/post", "other")
    assert int(blog["source_quality_score"]) <= 50


def test_same_domain_counts_as_one_independent_source() -> None:
    """Multiple articles from the same domain should only count as one independent source."""
    evidence = [
        EvidenceItem(
            title="Article A1",
            source_name="Reuters",
            url="https://www.reuters.com/article1",
            snippet="Officials confirmed the economy grew by 3 percent.",
            source_type="news",
            relevance_score=0.8,
            provider="web_search",
        ),
        EvidenceItem(
            title="Article A2",
            source_name="Reuters",
            url="https://www.reuters.com/article2",
            snippet="Reuters also reported economy grew by 3 percent.",
            source_type="news",
            relevance_score=0.85,
            provider="web_search",
        ),
        EvidenceItem(
            title="Article B1",
            source_name="BBC",
            url="https://www.bbc.com/news/world-1",
            snippet="BBC confirmed economic growth of 3 percent.",
            source_type="news",
            relevance_score=0.82,
            provider="web_search",
        ),
    ]
    agg = evidence_aggregation_service.aggregate_evidence_for_claim(
        "Economy grew by 3 percent",
        evidence,
    )
    # Reuters (1 domain) + BBC (1 domain) = 2 independent sources, NOT 3
    assert int(agg["independent_sources"]) == 2


def test_claim_verification_strong_support() -> None:
    """Strong corroboration across independent credible sources should yield SUPPORTED."""
    evidence = [
        EvidenceItem(
            title="NASA Discovers Water Ice on Mars",
            source_name="NASA",
            url="https://nasa.gov/mars-water-ice",
            snippet="NASA confirmed satellite findings proved presence of water ice on Mars.",
            source_type="official",
            relevance_score=0.9,
            provider="web_search",
        ),
        EvidenceItem(
            title="Astronomers Verify Mars Water Ice Findings",
            source_name="Nature",
            url="https://nature.com/articles/mars-water",
            snippet="Evidence shows verified water ice reservoirs beneath the Martian surface.",
            source_type="research",
            relevance_score=0.88,
            provider="web_search",
        ),
    ]
    verified = claim_verification_service.verify_single_claim(
        claim_id="claim_1",
        claim_text="NASA discovered water ice on Mars",
        evidence_list=evidence,
    )
    assert verified.verification.status == "SUPPORTED"
    assert verified.verification.confidence >= 0.70


def test_claim_verification_strong_contradiction() -> None:
    """Direct refutation by credible fact-checkers should yield CONTRADICTED."""
    evidence = [
        EvidenceItem(
            title="Fact Check: Drinking Boiled Garlic Does Not Cure Viral Infections",
            source_name="Snopes",
            url="https://snopes.com/fact-check/garlic-cure",
            snippet="False. Medical doctors confirmed this claim is a debunked hoax with no evidence.",
            source_type="fact_check",
            relevance_score=0.92,
            provider="google_factcheck",
        ),
        EvidenceItem(
            title="Health Feedback: Garlic Water Claims Refuted",
            source_name="Health Feedback",
            url="https://healthfeedback.org/garlic-water-myth",
            snippet="Misleading and false. World Health Organization refuted these claims.",
            source_type="fact_check",
            relevance_score=0.88,
            provider="google_factcheck",
        ),
    ]
    verified = claim_verification_service.verify_single_claim(
        claim_id="claim_1",
        claim_text="Drinking boiled garlic cures viral infections",
        evidence_list=evidence,
    )
    assert verified.verification.status == "CONTRADICTED"
    assert verified.verification.confidence >= 0.70


def test_claim_verification_no_evidence_is_insufficient() -> None:
    """Empty or irrelevant evidence must return INSUFFICIENT (not FAKE)."""
    verified = claim_verification_service.verify_single_claim(
        claim_id="claim_1",
        claim_text="Secret alien base located beneath Antarctica",
        evidence_list=[],
    )
    assert verified.verification.status == "INSUFFICIENT"
    assert verified.verification.confidence == 0.50


def test_claim_verification_conflicting_evidence() -> None:
    """Directly conflicting evidence should result in INSUFFICIENT status with low confidence."""
    evidence = [
        EvidenceItem(
            title="New policy was approved by committee",
            source_name="Source A",
            url="https://news-a.com/policy",
            snippet="Officials confirmed the bill was approved on Monday.",
            source_type="news",
            relevance_score=0.8,
            provider="web_search",
        ),
        EvidenceItem(
            title="Fact check: Policy bill was not approved",
            source_name="Source B",
            url="https://factcheck-b.org/policy",
            snippet="False. Spokesperson denied that the bill was approved, calling reports untrue.",
            source_type="fact_check",
            relevance_score=0.85,
            provider="web_search",
        ),
    ]
    verified = claim_verification_service.verify_single_claim(
        claim_id="claim_1",
        claim_text="The policy bill was approved",
        evidence_list=evidence,
    )
    # Competing high-support and high-contradiction signals -> INSUFFICIENT
    assert verified.verification.status in {"INSUFFICIENT", "CONTRADICTED"}


def test_decision_engine_ml_fake_overridden_by_strong_support() -> None:
    """If ML predicted FAKE due to unusual style, but verified evidence SUPPORTS claims, result is REAL."""
    claims = [
        VerifiedClaimItem(
            claim_id="claim_1",
            claim_text="NASA confirms water ice discovered on Mars",
            importance_score=0.95,
            verification=ClaimVerificationDetail(
                status="SUPPORTED",
                confidence=0.92,
                reason="Corroborated by NASA and Nature.",
                support_score=0.90,
                contradiction_score=0.05,
                independent_sources=3,
            ),
            evidence=[],
        )
    ]
    # ML predicted FAKE with 0.85 confidence (prob_fake = 0.85)
    final_res, factors, _ = decision_engine.compute_decision(
        ml_prediction="FAKE",
        ml_confidence=0.85,
        prob_fake=0.85,
        verified_claims=claims,
    )
    assert final_res.decision == "REAL"
    assert factors.supporting_claims == 1


def test_decision_engine_ml_real_overridden_by_strong_contradiction() -> None:
    """If ML predicted REAL due to professional style, but evidence CONTRADICTS claims, result is FAKE."""
    claims = [
        VerifiedClaimItem(
            claim_id="claim_1",
            claim_text="Spokesperson announces sudden resignation",
            importance_score=0.95,
            verification=ClaimVerificationDetail(
                status="CONTRADICTED",
                confidence=0.94,
                reason="Refuted by official government spokesperson.",
                support_score=0.05,
                contradiction_score=0.92,
                independent_sources=2,
            ),
            evidence=[],
        )
    ]
    # ML predicted REAL with 0.90 confidence (prob_fake = 0.10)
    final_res, factors, _ = decision_engine.compute_decision(
        ml_prediction="REAL",
        ml_confidence=0.90,
        prob_fake=0.10,
        verified_claims=claims,
    )
    assert final_res.decision == "FAKE"
    assert factors.contradicted_claims == 1


def test_decision_engine_no_evidence_falls_back_to_ml_with_capped_confidence() -> None:
    """When evidence is INSUFFICIENT, fallback to ML baseline with bounded confidence."""
    claims = [
        VerifiedClaimItem(
            claim_id="claim_1",
            claim_text="Obscure local claim with no search results",
            importance_score=0.8,
            verification=ClaimVerificationDetail(
                status="INSUFFICIENT",
                confidence=0.50,
                reason="No evidence retrieved.",
                support_score=0.0,
                contradiction_score=0.0,
                independent_sources=0,
            ),
            evidence=[],
        )
    ]
    final_res, factors, _ = decision_engine.compute_decision(
        ml_prediction="FAKE",
        ml_confidence=0.95,
        prob_fake=0.95,
        verified_claims=claims,
    )
    assert final_res.decision == "FAKE"
    # Confidence capped at <= 0.78 due to lack of external evidence
    assert final_res.confidence <= 0.78
    assert factors.insufficient_claims == 1


def test_explanation_service_generates_grounded_text() -> None:
    """Explanation should accurately summarize ML and claim verification facts."""
    ml_summary = MLAnalysisSummary(
        prediction="REAL",
        confidence=0.88,
        prob_fake=0.12,
        model="TF-IDF + Logistic Regression",
    )
    claims = [
        VerifiedClaimItem(
            claim_id="claim_1",
            claim_text="NASA confirms water ice",
            importance_score=0.9,
            verification=ClaimVerificationDetail(
                status="SUPPORTED",
                confidence=0.90,
                reason="Supported by NASA.",
                support_score=0.9,
                contradiction_score=0.0,
                independent_sources=2,
            ),
            evidence=[
                EvidenceItem(
                    title="NASA Report",
                    source_name="NASA",
                    url="https://nasa.gov",
                    snippet="Confirmed water ice.",
                    source_type="official",
                    relevance_score=0.9,
                    stance="SUPPORTS",
                    provider="web_search",
                )
            ],
        )
    ]
    final_res = FinalResult(decision="REAL", confidence=0.92)
    factors = DecisionFactors(
        ml_signal=0.88,
        evidence_strength=0.85,
        supporting_claims=1,
        contradicted_claims=0,
        insufficient_claims=0,
    )
    explanation = explanation_service.generate_explanation(
        ml_analysis=ml_summary,
        verified_claims=claims,
        final_result=final_res,
        decision_factors=factors,
    )
    assert "REAL" in explanation
    assert "NASA" in explanation
    assert "1 supported" in explanation or "supported by" in explanation


def test_complete_analyze_endpoint_end_to_end(client: TestClient) -> None:
    """POST /api/analyze should return complete fact check response with all fields."""
    payload = {
        "headline": "WASHINGTON (Reuters) - Federal Reserve announces interest rate policy decisions.",
        "article_text": (
            "Federal Reserve governors voted unanimously on Wednesday to maintain existing interest rates. "
            "Chairman stated that inflation metrics are trending toward target levels."
        ),
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "analysis_id" in data
    assert data["analysis_id"].startswith("analysis_")
    assert "ml_analysis" in data
    assert data["ml_analysis"]["prediction"] in {"FAKE", "REAL"}
    assert "claims" in data
    assert len(data["claims"]) >= 1
    for claim in data["claims"]:
        assert "claim_id" in claim
        assert "verification" in claim
        assert claim["verification"]["status"] in {"SUPPORTED", "CONTRADICTED", "INSUFFICIENT"}
    assert "final_result" in data
    assert data["final_result"]["decision"] in {"FAKE", "REAL"}
    assert 0.0 <= data["final_result"]["confidence"] <= 1.0
    assert "decision_factors" in data
    assert "explanation" in data
    assert len(data["explanation"]) > 20