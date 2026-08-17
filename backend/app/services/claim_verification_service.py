"""Claim Verification Service.

Evaluates aggregated evidence for each factual claim to produce a verified verdict:
SUPPORTED, CONTRADICTED, or INSUFFICIENT.
"""

from __future__ import annotations

from collections.abc import Sequence

from backend.app.models.schemas import (
    ClaimItem,
    ClaimStatus,
    ClaimVerificationDetail,
    EvidenceItem,
    VerifiedClaimItem,
)
from backend.app.services.evidence_aggregation_service import evidence_aggregation_service


class ClaimVerificationService:
    """Evaluates factual claims against multi-source evidence candidates."""

    def verify_single_claim(
        self,
        claim_id: str,
        claim_text: str,
        evidence_list: list[EvidenceItem],
        importance_score: float = 0.8,
    ) -> VerifiedClaimItem:
        """Evaluate evidence candidates to assign a verification status to a single claim."""
        agg = evidence_aggregation_service.aggregate_evidence_for_claim(claim_text, evidence_list)

        support_score = float(agg["support_score"])
        contradiction_score = float(agg["contradiction_score"])
        evidence_strength = float(agg["evidence_strength"])
        independent_sources = int(agg["independent_sources"])
        supporting_items = list(agg["supporting_evidence"])
        contradicting_items = list(agg["contradicting_evidence"])
        scored_evidence = list(agg["scored_evidence"])

        # 1. No evidence or extremely weak signal -> INSUFFICIENT
        if independent_sources == 0 or evidence_strength < 0.20:
            status: ClaimStatus = "INSUFFICIENT"
            confidence = 0.50
            reason = "No verifiable external evidence retrieved from independent sources."

        # 2. Strong contradiction out-weighing support -> CONTRADICTED
        elif contradiction_score >= 0.50 and contradiction_score > support_score * 1.3:
            status = "CONTRADICTED"
            confidence = round(min(0.98, max(0.68, contradiction_score)), 3)
            top_refuters = ", ".join(dict.fromkeys(item.source_name for item in contradicting_items[:2]))
            reason = (
                f"Contradicted by {len(contradicting_items)} independent source(s)"
                f"{f' including {top_refuters}' if top_refuters else ''}."
            )

        # 3. Strong corroboration out-weighing contradiction -> SUPPORTED
        elif support_score >= 0.50 and support_score > contradiction_score * 1.3:
            status = "SUPPORTED"
            confidence = round(min(0.98, max(0.68, support_score)), 3)
            top_supporters = ", ".join(dict.fromkeys(item.source_name for item in supporting_items[:2]))
            reason = (
                f"Corroborated by {len(supporting_items)} independent source(s)"
                f"{f' including {top_supporters}' if top_supporters else ''}."
            )

        # 4. Conflicting or mixed evidence -> INSUFFICIENT
        elif support_score >= 0.40 and contradiction_score >= 0.40:
            status = "INSUFFICIENT"
            confidence = 0.55
            reason = "Conflicting reporting detected: multiple sources present opposing claims."

        # 5. Low-signal / inconclusive evidence -> INSUFFICIENT
        else:
            status = "INSUFFICIENT"
            confidence = 0.50
            reason = "Retrieved background evidence is inconclusive or general context only."

        verification = ClaimVerificationDetail(
            status=status,
            confidence=confidence,
            reason=reason,
            support_score=support_score,
            contradiction_score=contradiction_score,
            independent_sources=independent_sources,
        )

        return VerifiedClaimItem(
            claim_id=claim_id,
            claim_text=claim_text,
            importance_score=importance_score,
            verification=verification,
            evidence=scored_evidence,
        )

    def verify_all_claims(
        self,
        claims: Sequence[ClaimItem],
        evidence_map: dict[str, list[EvidenceItem]],
    ) -> list[VerifiedClaimItem]:
        """Verify an entire list of claims against their mapped evidence citations."""
        verified_list: list[VerifiedClaimItem] = []
        for claim in claims:
            ev_list = evidence_map.get(claim.claim_id, [])
            verified_item = self.verify_single_claim(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                evidence_list=ev_list,
                importance_score=claim.importance_score,
            )
            verified_list.append(verified_item)
        return verified_list


# Singleton instance
claim_verification_service = ClaimVerificationService()