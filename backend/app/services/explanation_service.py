"""Explainability and Fact-Check Rationale Generation Service.

Synthesizes structured explanations grounded strictly in the ML probabilities,
claim verification statuses, and retrievable evidence citations.
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.models.schemas import (
    DecisionFactors,
    FinalResult,
    MLAnalysisSummary,
    VerifiedClaimItem,
)


class ExplanationService:
    """Generates concise, human-readable fact-check explanations from analysis data."""

    def generate_explanation(
        self,
        ml_analysis: MLAnalysisSummary,
        verified_claims: Sequence[VerifiedClaimItem],
        final_result: FinalResult,
        decision_factors: DecisionFactors,
    ) -> str:
        """Construct a structured, data-grounded natural-language summary."""
        parts: list[str] = []

        # 1. ML Stylistic Baseline
        ml_pct = int(ml_analysis.confidence * 100)
        parts.append(
            f"Stylistic ML analysis evaluated the text as {ml_analysis.prediction} ({ml_pct}% confidence)."
        )

        total_claims = len(verified_claims)
        if total_claims == 0:
            parts.append(
                "No verifiable factual claims were extracted. "
                "The final result relies exclusively on stylistic machine learning patterns."
            )
            return " ".join(parts)

        # 2. Claim Breakdown
        supp_count = decision_factors.supporting_claims
        contra_count = decision_factors.contradicted_claims
        insuff_count = decision_factors.insufficient_claims

        # Collect unique source names cited across claims
        supporting_sources: list[str] = []
        contradicting_sources: list[str] = []

        for c in verified_claims:
            for ev in c.evidence:
                if ev.stance == "SUPPORTS" and ev.source_name not in supporting_sources:
                    supporting_sources.append(ev.source_name)
                elif ev.stance == "CONTRADICTS" and ev.source_name not in contradicting_sources:
                    contradicting_sources.append(ev.source_name)

        claim_summary_parts = []
        if supp_count > 0:
            src_str = f" ({', '.join(supporting_sources[:2])})" if supporting_sources else ""
            claim_summary_parts.append(f"{supp_count} supported by independent reporting{src_str}")
        if contra_count > 0:
            src_str = f" ({', '.join(contradicting_sources[:2])})" if contradicting_sources else ""
            claim_summary_parts.append(f"{contra_count} contradicted by external sources{src_str}")
        if insuff_count > 0:
            claim_summary_parts.append(f"{insuff_count} with insufficient external evidence")

        parts.append(
            f"Identified {total_claims} factual claim(s): {', '.join(claim_summary_parts)}."
        )

        # 3. Decision Justification
        final_pct = int(final_result.confidence * 100)
        if contra_count > 0:
            if ml_analysis.prediction == "REAL":
                parts.append(
                    f"Although linguistic style resembled authentic news, credible external refutations "
                    f"outweighed stylistic cues, yielding a final {final_result.decision} verdict ({final_pct}% confidence)."
                )
            else:
                parts.append(
                    f"Corroborating refutations reinforced the stylistic risk markers, confirming the "
                    f"final {final_result.decision} verdict ({final_pct}% confidence)."
                )
        elif supp_count > 0:
            if ml_analysis.prediction == "FAKE":
                parts.append(
                    f"Although stylistic traits flagged potential risk, verified independent reporting "
                    f"substantiated the core assertions, resulting in a final {final_result.decision} verdict ({final_pct}% confidence)."
                )
            else:
                parts.append(
                    f"Credible reporting corroborated the assertions alongside authentic writing style, "
                    f"confirming the final {final_result.decision} verdict ({final_pct}% confidence)."
                )
        else:
            parts.append(
                f"External evidence was insufficient to independently corroborate the claims. "
                f"The final {final_result.decision} verdict reflects the baseline model analysis with bounded confidence ({final_pct}%)."
            )

        return " ".join(parts)


# Singleton instance
explanation_service = ExplanationService()