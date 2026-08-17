"""Evidence Aggregation and Domain Grouping Service.

Aggregates evidence across independent sources, eliminates domain-level repetition,
and calculates weighted support, contradiction, and strength metrics.
"""

from __future__ import annotations

from urllib.parse import urlparse

from backend.app.models.schemas import EvidenceItem
from backend.app.services.evidence_analyzer import evidence_analyzer
from backend.app.services.source_scoring_service import source_scoring_service


def extract_domain(url: str) -> str:
    """Extract clean base domain from URL for independent source counting."""
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url.lower()


class EvidenceAggregationService:
    """Aggregates and scores candidate evidence items for a given claim."""

    def aggregate_evidence_for_claim(
        self,
        claim_text: str,
        evidence_list: list[EvidenceItem],
    ) -> dict[str, object]:
        """Process, score, and aggregate evidence candidates for one claim.

        Ensures multiple articles from the same domain count as ONE independent source.
        """
        if not evidence_list:
            return {
                "support_score": 0.0,
                "contradiction_score": 0.0,
                "evidence_strength": 0.0,
                "independent_sources": 0,
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "neutral_evidence": [],
                "scored_evidence": [],
            }

        # 1. Score each evidence candidate
        scored_evidence: list[EvidenceItem] = []
        domain_groups: dict[str, list[tuple[EvidenceItem, float, str]]] = {}

        for item in evidence_list:
            # Score source quality
            quality_info = source_scoring_service.score_source(
                source_name=item.source_name,
                url=item.url,
                source_type=item.source_type,
                publication_date=item.publication_date,
            )
            item.source_quality_score = int(quality_info["source_quality_score"])

            # Evaluate stance relative to claim
            stance_info = evidence_analyzer.evaluate_stance(claim_text, item)
            stance = str(stance_info["stance"])
            alignment = float(stance_info["alignment_score"])
            item.stance = stance

            scored_evidence.append(item)

            # Group by domain
            domain = extract_domain(item.url) or item.source_name.lower()
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append((item, alignment, stance))

        # 2. Domain-level aggregation: each independent domain votes once based on its strongest signal
        independent_sources_count = len(domain_groups)
        total_support_weight = 0.0
        total_contradiction_weight = 0.0
        total_quality_mass = 0.0

        supporting_items: list[EvidenceItem] = []
        contradicting_items: list[EvidenceItem] = []
        neutral_items: list[EvidenceItem] = []

        for _domain, items_in_domain in domain_groups.items():
            # Find the strongest signal in this domain
            best_item, best_alignment, best_stance = max(
                items_in_domain,
                key=lambda x: (x[0].relevance_score * (x[0].source_quality_score / 100.0) * x[1]),
            )

            effective_quality = best_item.source_quality_score / 100.0
            domain_signal_strength = best_item.relevance_score * effective_quality * best_alignment
            total_quality_mass += effective_quality

            if best_stance == "CONTRADICTS":
                total_contradiction_weight += domain_signal_strength
                contradicting_items.append(best_item)
            elif best_stance == "SUPPORTS":
                total_support_weight += domain_signal_strength
                supporting_items.append(best_item)
            else:
                neutral_items.append(best_item)

        # 3. Compute normalized aggregate scores
        # Scaling factor based on number of independent corroborating sources
        source_scaling = min(1.0, independent_sources_count / 3.0)

        # Support score (0.0 - 1.0)
        support_score = round(min(1.0, total_support_weight * (0.8 + 0.2 * source_scaling)), 3)
        # Contradiction score (0.0 - 1.0)
        contradiction_score = round(min(1.0, total_contradiction_weight * (0.8 + 0.2 * source_scaling)), 3)

        # Evidence strength: overall volume and quality of retrieved data
        avg_quality = (total_quality_mass / max(independent_sources_count, 1))
        evidence_strength = round(min(1.0, (independent_sources_count * 0.25) * avg_quality), 3)

        return {
            "support_score": support_score,
            "contradiction_score": contradiction_score,
            "evidence_strength": evidence_strength,
            "independent_sources": independent_sources_count,
            "supporting_evidence": supporting_items,
            "contradicting_evidence": contradicting_items,
            "neutral_evidence": neutral_items,
            "scored_evidence": scored_evidence,
        }


# Singleton instance
evidence_aggregation_service = EvidenceAggregationService()