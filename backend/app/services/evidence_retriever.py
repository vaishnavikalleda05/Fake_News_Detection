"""Multi-source Evidence Retriever Service.

Orchestrates live queries across fact-checking tools, web search, and encyclopedia
knowledge bases with deduplication, ranking, and resilient error isolation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from backend.app.config import settings
from backend.app.models.schemas import ClaimItem, EvidenceItem
from backend.app.providers.base_provider import (
    BaseEvidenceProvider,
    compute_relevance_score,
    normalize_url,
)
from backend.app.providers.google_factcheck import GoogleFactCheckProvider
from backend.app.providers.web_search import WebSearchProvider
from backend.app.providers.wikipedia_provider import WikipediaProvider
from backend.app.utils.logger import logger


class EvidenceRetrieverService:
    """Coordinates multi-source evidence candidate retrieval and aggregation."""

    def __init__(
        self,
        providers: Sequence[BaseEvidenceProvider] | None = None,
        default_max_evidence: int | None = None,
    ) -> None:
        self.providers: list[BaseEvidenceProvider] = list(providers) if providers is not None else [
            GoogleFactCheckProvider(),
            WebSearchProvider(),
            WikipediaProvider(),
        ]
        self.default_max_evidence = default_max_evidence or settings.MAX_EVIDENCE_PER_CLAIM

    def get_available_providers(self) -> list[str]:
        """Return list of names of currently active/available providers."""
        return [p.name for p in self.providers if p.is_available()]

    async def retrieve_evidence_for_single_claim(
        self,
        claim_text: str,
        max_evidence: int | None = None,
    ) -> list[EvidenceItem]:
        """Query all available providers concurrently for a single claim.

        Aggregates, deduplicates, and ranks evidence candidates by relevance.
        """
        limit = max_evidence or self.default_max_evidence
        if not claim_text or not claim_text.strip():
            return []

        active_providers = [p for p in self.providers if p.is_available()]
        if not active_providers:
            logger.warning("No active evidence providers available.")
            return []

        # Launch provider queries concurrently with error isolation
        tasks = [
            provider.search_evidence(claim_text.strip(), max_results=limit)
            for provider in active_providers
        ]
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        raw_items: list[EvidenceItem] = []
        for provider, result in zip(active_providers, results_nested, strict=False):
            if isinstance(result, Exception):
                logger.warning("Provider '%s' raised exception during retrieval: %s", provider.name, result)
            elif isinstance(result, list):
                raw_items.extend(result)

        if not raw_items:
            return []

        # Deduplication
        seen_urls: set[str] = set()
        seen_source_titles: set[tuple[str, str]] = set()
        unique_items: list[EvidenceItem] = []

        for item in raw_items:
            norm_url = normalize_url(item.url)
            source_title_key = (item.source_name.strip().lower(), item.title.strip().lower())

            if norm_url and norm_url in seen_urls:
                continue
            if source_title_key in seen_source_titles:
                continue

            if norm_url:
                seen_urls.add(norm_url)
            seen_source_titles.add(source_title_key)

            # Ensure relevance score is calculated against current claim
            if item.relevance_score <= 0.0 or item.relevance_score == 0.5:
                item.relevance_score = compute_relevance_score(
                    claim_text=claim_text,
                    title=item.title,
                    snippet=item.snippet,
                )

            unique_items.append(item)

        # Rank evidence candidates by relevance score descending
        # Give higher initial priority to verified fact-checks, then news/research, then encyclopedia
        def _sort_key(item: EvidenceItem) -> tuple[int, float]:
            priority_map = {
                "fact_check": 3,
                "official": 2,
                "research": 2,
                "news": 1,
                "encyclopedia": 0,
                "other": 0,
            }
            type_weight = priority_map.get(item.source_type, 0)
            return (type_weight, item.relevance_score)

        unique_items.sort(key=_sort_key, reverse=True)

        return unique_items[:limit]

    async def retrieve_evidence_for_claims(
        self,
        claims: Sequence[ClaimItem],
        max_evidence_per_claim: int | None = None,
    ) -> dict[str, list[EvidenceItem]]:
        """Retrieve evidence for a list of claims in parallel.

        Returns:
            dict mapping claim_id to a list of EvidenceItem instances.
        """
        if not claims:
            return {}

        limit = max_evidence_per_claim or self.default_max_evidence
        tasks = [
            self.retrieve_evidence_for_single_claim(claim.claim_text, max_evidence=limit)
            for claim in claims
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        evidence_map: dict[str, list[EvidenceItem]] = {}
        for claim, res in zip(claims, results, strict=False):
            if isinstance(res, Exception):
                logger.warning("Retrieval failed for claim '%s': %s", claim.claim_id, res)
                evidence_map[claim.claim_id] = []
            elif isinstance(res, list):
                evidence_map[claim.claim_id] = res
            else:
                evidence_map[claim.claim_id] = []

        return evidence_map


# Singleton instance
evidence_retriever = EvidenceRetrieverService()