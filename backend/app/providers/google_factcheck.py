"""Google Fact Check Tools API Provider.

Retrieves verified claims and ratings from professional fact-checking organizations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from backend.app.config import settings
from backend.app.models.schemas import EvidenceItem
from backend.app.providers.base_provider import (
    BaseEvidenceProvider,
    clean_snippet_html,
    compute_relevance_score,
    normalize_url,
)
from backend.app.utils.logger import logger


_FACTCHECK_SEARCH_URL = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)


class GoogleFactCheckProvider(BaseEvidenceProvider):
    """Integrates with Google Fact Check Tools API."""

    # Sentinel used to distinguish:
    #
    # GoogleFactCheckProvider()
    #     -> use configured environment/API key
    #
    # GoogleFactCheckProvider(api_key=None)
    #     -> explicitly disable the API key
    _USE_CONFIGURED_KEY = object()

    def __init__(
        self,
        api_key: str | None | Any = _USE_CONFIGURED_KEY,
        timeout: float | None = None,
    ) -> None:
        """Initialize the Google Fact Check provider."""

        if api_key is self._USE_CONFIGURED_KEY:
            # Normal application behaviour:
            # use the key configured in settings/.env
            self.api_key = settings.GOOGLE_FACTCHECK_API_KEY
        else:
            # Explicitly supplied value.
            # None means no API key.
            self.api_key = api_key

        self.timeout = (
            timeout
            if timeout is not None
            else settings.EVIDENCE_TIMEOUT_SECONDS
        )

    @property
    def name(self) -> str:
        """Return provider name."""
        return "google_factcheck"

    def is_available(self) -> bool:
        """Return True only when a non-empty API key is configured."""

        return bool(
            self.api_key
            and isinstance(self.api_key, str)
            and self.api_key.strip()
        )

    async def search_evidence(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[EvidenceItem]:
        """Search Google Fact Check API for reviews matching a claim."""

        # Do not make an API request when the provider is unavailable.
        if not self.is_available():
            return []

        # Reject empty queries.
        if not query or not query.strip():
            return []

        params = {
            "query": query.strip(),
            "key": self.api_key,
            "languageCode": "en",
            "pageSize": max_results,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.get(
                    _FACTCHECK_SEARCH_URL,
                    params=params,
                )

                if response.status_code != 200:
                    logger.warning(
                        "Google Fact Check API returned HTTP %s: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return []

                data = response.json()

                raw_claims = data.get("claims", [])

                evidence_list: list[EvidenceItem] = []

                for claim_data in raw_claims:

                    claim_text = claim_data.get("text", "")

                    claim_reviews = claim_data.get(
                        "claimReview",
                        [],
                    )

                    for review in claim_reviews:

                        review_url = review.get("url")

                        if not review_url:
                            continue

                        publisher = review.get(
                            "publisher",
                            {},
                        )

                        source_name = (
                            publisher.get("name")
                            or publisher.get("site")
                            or "Fact Check Organization"
                        )

                        title = (
                            review.get("title")
                            or f"Fact Check: {claim_text}"
                        )

                        textual_rating = review.get(
                            "textualRating",
                            "Unrated",
                        )

                        snippet = (
                            f'Verified Claim: "{claim_text}" '
                            f"— Rating by {source_name}: "
                            f"{textual_rating}"
                        )

                        pub_date = review.get(
                            "reviewDate"
                        )

                        relevance = compute_relevance_score(
                            claim_text=query,
                            title=title,
                            snippet=(
                                f"{claim_text} "
                                f"{textual_rating}"
                            ),
                        )

                        evidence_list.append(
                            EvidenceItem(
                                title=clean_snippet_html(
                                    title
                                ),
                                source_name=source_name,
                                url=normalize_url(
                                    review_url
                                ),
                                snippet=clean_snippet_html(
                                    snippet
                                ),
                                source_type="fact_check",
                                publication_date=pub_date,
                                retrieval_timestamp=(
                                    datetime.now(
                                        timezone.utc
                                    ).isoformat()
                                ),
                                relevance_score=relevance,
                                provider=self.name,
                            )
                        )

                        if len(evidence_list) >= max_results:
                            break

                    if len(evidence_list) >= max_results:
                        break

                return evidence_list

        except httpx.TimeoutException:
            logger.warning(
                "Google Fact Check API timed out for query: %s",
                query[:50],
            )
            return []

        except Exception as exc:
            logger.warning(
                "Google Fact Check API query failed: %s",
                exc,
            )
            return []