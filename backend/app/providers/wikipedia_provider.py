"""Wikipedia API Evidence Provider.

Queries Wikipedia's OpenSearch and Search API to retrieve background encyclopedia
evidence and contextual verification candidates.
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

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

_WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"


class WikipediaProvider(BaseEvidenceProvider):
    """Retrieves encyclopedia summaries and entity information from Wikipedia."""

    def __init__(self, user_agent: str | None = None, timeout: float | None = None) -> None:
        self.user_agent = user_agent or settings.WIKIPEDIA_USER_AGENT
        self.timeout = timeout or settings.EVIDENCE_TIMEOUT_SECONDS

    @property
    def name(self) -> str:
        return "wikipedia"

    def is_available(self) -> bool:
        """Wikipedia public API is always available."""
        return True

    async def search_evidence(self, query: str, max_results: int = 5) -> list[EvidenceItem]:
        """Search Wikipedia articles matching the claim query."""
        if not query or not query.strip():
            return []

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query.strip(),
            "format": "json",
            "utf8": "1",
            "srlimit": max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(_WIKIPEDIA_API_URL, params=params)
                if response.status_code != 200:
                    logger.warning("Wikipedia API returned HTTP %s", response.status_code)
                    return []

                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                evidence_list: list[EvidenceItem] = []

                for item in search_results:
                    title = item.get("title", "")
                    raw_snippet = item.get("snippet", "")
                    timestamp = item.get("timestamp")
                    if not title:
                        continue

                    # Construct canonical Wikipedia article URL
                    encoded_title = quote(title.replace(" ", "_"))
                    page_url = f"https://en.wikipedia.org/wiki/{encoded_title}"
                    clean_snip = clean_snippet_html(raw_snippet)

                    relevance = compute_relevance_score(
                        claim_text=query,
                        title=title,
                        snippet=clean_snip,
                    )

                    evidence_list.append(
                        EvidenceItem(
                            title=title,
                            source_name="Wikipedia",
                            url=normalize_url(page_url),
                            snippet=clean_snip or f"Wikipedia article on {title}.",
                            source_type="encyclopedia",
                            publication_date=timestamp,
                            retrieval_timestamp=datetime.now(timezone.utc).isoformat(),
                            relevance_score=relevance,
                            provider=self.name,
                        )
                    )

                    if len(evidence_list) >= max_results:
                        break

                return evidence_list

        except httpx.TimeoutException:
            logger.warning("Wikipedia search timed out for query: %s", query[:50])
            return []
        except Exception as exc:
            logger.warning("Wikipedia API search failed: %s", exc)
            return []