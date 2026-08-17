"""Web Search Provider.

Retrieves real-time external web and news search results using configured APIs
(Tavily, SerpAPI, Bing) or public DuckDuckGo fallback search.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

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

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _infer_source_name_and_type(url: str, title: str) -> tuple[str, str]:
    """Extract domain source name and infer source type category."""
    try:
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Known source classifications
        if any(d in domain for d in ("gov", "who.int", "cdc.gov", "un.org", "nasa.gov", "whitehouse.gov")):
            source_type = "official"
        elif any(d in domain for d in ("reuters.com", "apnews.com", "bbc.com", "cnn.com", "nytimes.com", "theguardian.com", "washingtonpost.com", "bloomberg.com", "npr.org")):
            source_type = "news"
        elif any(d in domain for d in ("nature.com", "sciencedirect.com", "ncbi.nlm.nih.gov", "arxiv.org", "thelancet.com")):
            source_type = "research"
        elif any(d in domain for d in ("snopes.com", "politifact.com", "factcheck.org", "fullfact.org")):
            source_type = "fact_check"
        elif "wikipedia.org" in domain:
            source_type = "encyclopedia"
        else:
            source_type = "news" if any(term in domain for term in ("news", "times", "post", "tribune", "daily", "journal")) else "other"

        # Format domain as readable source name (e.g. reuters.com -> Reuters)
        source_parts = domain.split(".")
        main_name = source_parts[0].capitalize() if source_parts else domain
        return main_name, source_type
    except Exception:
        return "Web Source", "news"


class WebSearchProvider(BaseEvidenceProvider):
    """Retrieves live web and news evidence candidates from search engines."""

    def __init__(
        self,
        tavily_key: str | None = None,
        serpapi_key: str | None = None,
        bing_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.tavily_key = tavily_key or settings.TAVILY_API_KEY
        self.serpapi_key = serpapi_key or settings.SERPAPI_API_KEY
        self.bing_key = bing_key or settings.BING_SEARCH_API_KEY
        self.timeout = timeout or settings.EVIDENCE_TIMEOUT_SECONDS

    @property
    def name(self) -> str:
        return "web_search"

    def is_available(self) -> bool:
        """Always available (via API key or public search fallback)."""
        return True

    async def search_evidence(self, query: str, max_results: int = 5) -> list[EvidenceItem]:
        """Execute web search across available backends."""
        if not query or not query.strip():
            return []

        # 1. Try Tavily if configured
        if self.tavily_key and self.tavily_key.strip():
            results = await self._search_tavily(query, max_results)
            if results:
                return results

        # 2. Try SerpAPI if configured
        if self.serpapi_key and self.serpapi_key.strip():
            results = await self._search_serpapi(query, max_results)
            if results:
                return results

        # 3. Try Bing if configured
        if self.bing_key and self.bing_key.strip():
            results = await self._search_bing(query, max_results)
            if results:
                return results

        # 4. Fallback to DuckDuckGo public search
        return await self._search_duckduckgo(query, max_results)

    async def _search_tavily(self, query: str, max_results: int) -> list[EvidenceItem]:
        """Query Tavily Search API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "api_key": self.tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "include_answer": False,
                    "max_results": max_results,
                }
                res = await client.post("https://api.tavily.com/search", json=payload)
                if res.status_code != 200:
                    logger.warning("Tavily search returned %s", res.status_code)
                    return []

                data = res.json()
                items: list[EvidenceItem] = []
                for item in data.get("results", []):
                    url = item.get("url")
                    title = item.get("title") or "Web Search Result"
                    snippet = item.get("content") or ""
                    if not url:
                        continue

                    source_name, source_type = _infer_source_name_and_type(url, title)
                    relevance = compute_relevance_score(query, title, snippet)
                    items.append(
                        EvidenceItem(
                            title=clean_snippet_html(title),
                            source_name=source_name,
                            url=normalize_url(url),
                            snippet=clean_snippet_html(snippet),
                            source_type=source_type,
                            relevance_score=relevance,
                            provider=self.name,
                        )
                    )
                return items
        except Exception as exc:
            logger.warning("Tavily search query failed: %s", exc)
            return []

    async def _search_serpapi(self, query: str, max_results: int) -> list[EvidenceItem]:
        """Query SerpAPI Google search."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    "api_key": self.serpapi_key,
                    "q": query,
                    "num": max_results,
                    "engine": "google",
                }
                res = await client.get("https://serpapi.com/search", params=params)
                if res.status_code != 200:
                    return []
                data = res.json()
                items: list[EvidenceItem] = []
                for item in data.get("organic_results", [])[:max_results]:
                    url = item.get("link")
                    title = item.get("title") or ""
                    snippet = item.get("snippet") or ""
                    if not url:
                        continue
                    source_name, source_type = _infer_source_name_and_type(url, title)
                    relevance = compute_relevance_score(query, title, snippet)
                    items.append(
                        EvidenceItem(
                            title=clean_snippet_html(title),
                            source_name=source_name,
                            url=normalize_url(url),
                            snippet=clean_snippet_html(snippet),
                            source_type=source_type,
                            relevance_score=relevance,
                            provider=self.name,
                        )
                    )
                return items
        except Exception as exc:
            logger.warning("SerpAPI search failed: %s", exc)
            return []

    async def _search_bing(self, query: str, max_results: int) -> list[EvidenceItem]:
        """Query Bing Web Search API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Ocp-Apim-Subscription-Key": self.bing_key or ""}
                params = {"q": query, "count": max_results}
                res = await client.get("https://api.bing.microsoft.com/v7.0/search", headers=headers, params=params)
                if res.status_code != 200:
                    return []
                data = res.json()
                items: list[EvidenceItem] = []
                for item in data.get("webPages", {}).get("value", [])[:max_results]:
                    url = item.get("url")
                    title = item.get("name") or ""
                    snippet = item.get("snippet") or ""
                    if not url:
                        continue
                    source_name, source_type = _infer_source_name_and_type(url, title)
                    relevance = compute_relevance_score(query, title, snippet)
                    items.append(
                        EvidenceItem(
                            title=clean_snippet_html(title),
                            source_name=source_name,
                            url=normalize_url(url),
                            snippet=clean_snippet_html(snippet),
                            source_type=source_type,
                            relevance_score=relevance,
                            provider=self.name,
                        )
                    )
                return items
        except Exception as exc:
            logger.warning("Bing search failed: %s", exc)
            return []

    async def _search_duckduckgo(self, query: str, max_results: int) -> list[EvidenceItem]:
        """Fallback public search using DuckDuckGo endpoints."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=_DEFAULT_HEADERS, follow_redirects=True) as client:
                # 1. Try DuckDuckGo Lite endpoint
                res = await client.post("https://lite.duckduckgo.com/lite/", data={"q": query})
                if res.status_code == 200:
                    html = res.text
                    # Lite format: <a class="result-link" href="...">Title</a> ... <td class="result-snippet">Snippet</td>
                    links = re.findall(r'<a[^>]*class=["\']result-link["\'][^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
                    snippets = re.findall(r'<td[^>]*class=["\']result-snippet["\'][^>]*>(.*?)</td>', html, re.DOTALL)

                    items: list[EvidenceItem] = []
                    for idx, (raw_href, raw_title) in enumerate(links[:max_results]):
                        match_uddg = re.search(r"uddg=([^&]+)", raw_href)
                        actual_url = unquote(match_uddg.group(1)) if match_uddg else raw_href

                        if not actual_url.startswith(("http://", "https://")):
                            continue

                        title = clean_snippet_html(raw_title)
                        snippet = clean_snippet_html(snippets[idx]) if idx < len(snippets) else ""
                        source_name, source_type = _infer_source_name_and_type(actual_url, title)
                        relevance = compute_relevance_score(query, title, snippet)

                        items.append(
                            EvidenceItem(
                                title=title or "Web Search Result",
                                source_name=source_name,
                                url=normalize_url(actual_url),
                                snippet=snippet,
                                source_type=source_type,
                                relevance_score=relevance,
                                provider=self.name,
                            )
                        )
                    if items:
                        return items

                # 2. Fallback to HTML endpoint
                res_html = await client.post("https://html.duckduckgo.com/html/", data={"q": query})
                if res_html.status_code == 200:
                    html = res_html.text
                    raw_results = re.findall(
                        r'<a[^>]*class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
                        r'<a[^>]*class="result__snippet[^"]*"[^>]*>(.*?)</a>',
                        html,
                        flags=re.DOTALL,
                    )
                    items_html: list[EvidenceItem] = []
                    for link_href, raw_title_or_url, raw_snippet in raw_results[:max_results]:
                        match_uddg = re.search(r"uddg=([^&]+)", link_href)
                        actual_url = unquote(match_uddg.group(1)) if match_uddg else link_href

                        if not actual_url.startswith(("http://", "https://")):
                            continue

                        title = clean_snippet_html(raw_title_or_url)
                        snippet = clean_snippet_html(raw_snippet)
                        source_name, source_type = _infer_source_name_and_type(actual_url, title)
                        relevance = compute_relevance_score(query, title, snippet)

                        items_html.append(
                            EvidenceItem(
                                title=title or "Web Search Result",
                                source_name=source_name,
                                url=normalize_url(actual_url),
                                snippet=snippet,
                                source_type=source_type,
                                relevance_score=relevance,
                                provider=self.name,
                            )
                        )
                    return items_html

                return []
        except httpx.TimeoutException:
            logger.warning("DuckDuckGo search timed out for query: %s", query[:50])
            return []
        except Exception as exc:
            logger.warning("DuckDuckGo search failed: %s", exc)
            return []