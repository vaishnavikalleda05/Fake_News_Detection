"""Hybrid Decision Engine.

Synthesizes stylistic Machine Learning probabilities and multi-source claim verification
into a deterministic, explainable final verdict: FAKE or REAL.
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.models.schemas import (
    DecisionFactors,
    FinalDecisionType,
    FinalResult,
    VerifiedClaimItem,
)


class DecisionEngine:
    """Combines ML confidence, claim verification outcomes, and evidence strength."""

    # Transparent Baseline Weights
    ML_WEIGHT_WITH_EVIDENCE = 0.35
    EVIDENCE_WEIGHT = 0.65

    def compute_decision(
        self,
        ml_prediction: str,
        ml_confidence: float,
        prob_fake: float,
        verified_claims: Sequence[VerifiedClaimItem],
    ) -> tuple[FinalResult, DecisionFactors, str]:
        """Compute the final FAKE or REAL decision and output decision factors.

        Args:
            ml_prediction: 'FAKE' or 'REAL' from the ML baseline.
            ml_confidence: Confidence score of the ML prediction (0.5 to 1.0).
            prob_fake: Raw fake probability from ML model (0.0 to 1.0).
            verified_claims: List of VerifiedClaimItem instances.

        Returns:
            Tuple of (FinalResult, DecisionFactors, brief_reason).
        """
        # 1. Map ML signal to continuous Real scale (0.0 = fake style, 1.0 = real style)
        ml_signal_real = round(1.0 - prob_fake, 4)

        # 2. Count claim states and compute evidence synthesis
        supporting_count = sum(1 for c in verified_claims if c.verification.status == "SUPPORTED")
        contradicted_count = sum(1 for c in verified_claims if c.verification.status == "CONTRADICTED")
        insufficient_count = sum(1 for c in verified_claims if c.verification.status == "INSUFFICIENT")

        total_weight = 0.0
        weighted_evidence_real = 0.0
        total_support_scores = 0.0
        total_contradiction_scores = 0.0

        for claim in verified_claims:
            w = max(0.1, claim.importance_score)
            total_weight += w
            total_support_scores += claim.verification.support_score * w
            total_contradiction_scores += claim.verification.contradiction_score * w

            if claim.verification.status == "SUPPORTED":
                # Real signal: confidence (e.g. 0.85 -> 0.85)
                weighted_evidence_real += w * claim.verification.confidence
            elif claim.verification.status == "CONTRADICTED":
                # Fake signal: (1 - confidence) (e.g. 0.85 -> 0.15)
                weighted_evidence_real += w * (1.0 - claim.verification.confidence)
            else:  # INSUFFICIENT
                weighted_evidence_real += w * 0.50

        has_claims = bool(verified_claims)
        avg_support = (total_support_scores / total_weight) if total_weight > 0 else 0.0
        avg_contradiction = (total_contradiction_scores / total_weight) if total_weight > 0 else 0.0
        evidence_real_score = (weighted_evidence_real / total_weight) if total_weight > 0 else 0.50

        # Overall evidence strength metric (volume and clarity of verified/contradicted claims)
        has_definitive_evidence = (supporting_count > 0 or contradicted_count > 0)
        evidence_strength = round(
            min(1.0, (avg_support + avg_contradiction) * (1.0 if has_definitive_evidence else 0.4)),
            3,
        )

        # 3. Apply Decision Fusion Formula
        if has_claims and (has_definitive_evidence or evidence_strength >= 0.25):
            # Evidence is available and actively influences the outcome
            combined_real = (
                (self.ML_WEIGHT_WITH_EVIDENCE * ml_signal_real)
                + (self.EVIDENCE_WEIGHT * evidence_real_score)
            )

            # Guardrail 1: Heavy contradiction by credible sources strictly yields FAKE
            if contradicted_count > 0 and contradicted_count >= supporting_count:
                combined_real = min(combined_real, 0.25)

            # Guardrail 2: Heavy corroboration by credible sources strictly yields REAL
            if supporting_count > 0 and supporting_count > contradicted_count:
                combined_real = max(combined_real, 0.75)

            if combined_real >= 0.50:
                final_decision: FinalDecisionType = "REAL"
                final_confidence = min(0.98, max(0.55, combined_real))
            else:
                final_decision = "FAKE"
                final_confidence = min(0.98, max(0.55, 1.0 - combined_real))

            if contradicted_count > 0:
                reason = f"Classified as FAKE because {contradicted_count} claim(s) were contradicted by verified reporting."
            elif supporting_count > 0:
                reason = f"Classified as REAL because {supporting_count} claim(s) were corroborated by independent reporting."
            else:
                reason = "Classification weighed combined linguistic pattern and multi-source evidence indicators."

        else:
            # Evidence is insufficient: fallback to ML baseline with lower confidence cap
            if ml_signal_real >= 0.50:
                final_decision = "REAL"
                final_confidence = min(0.78, max(0.55, ml_confidence))
            else:
                final_decision = "FAKE"
                final_confidence = min(0.78, max(0.55, ml_confidence))

            reason = "External evidence was insufficient; classification relies primarily on stylistic ML indicators with bounded confidence."

        decision_factors = DecisionFactors(
            ml_signal=ml_signal_real,
            evidence_strength=evidence_strength,
            supporting_claims=supporting_count,
            contradicted_claims=contradicted_count,
            insufficient_claims=insufficient_count,
            claim_support_score=round(avg_support, 3),
            claim_contradiction_score=round(avg_contradiction, 3),
        )

        final_result = FinalResult(
            decision=final_decision,
            confidence=round(final_confidence, 4),
        )

        return final_result, decision_factors, reason


# Singleton instance
decision_engine = DecisionEngine()