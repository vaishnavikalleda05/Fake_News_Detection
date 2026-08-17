"""Tests for multi-source evidence providers and retriever service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.schemas import ClaimItem, EvidenceItem
from backend.app.providers.base_provider import (
    BaseEvidenceProvider,
    clean_snippet_html,
    compute_relevance_score,
    normalize_url,
)
from backend.app.providers.google_factcheck import GoogleFactCheckProvider
from backend.app.providers.wikipedia_provider import WikipediaProvider
from backend.app.services.evidence_retriever import EvidenceRetrieverService


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_url_normalization() -> None:
    """URLs should have tracking parameters and fragments stripped."""
    raw = "https://www.example.com/article?utm_source=twitter&utm_medium=social&id=123#section"
    normalized = normalize_url(raw)
    assert "utm_source" not in normalized
    assert "utm_medium" not in normalized
    assert "#section" not in normalized
    assert "id=123" in normalized


def test_html_cleaning() -> None:
    """HTML tags and entity references should be cleanly removed."""
    raw = "Scientists have <b>discovered</b> new evidence &amp; verified the claim."
    assert clean_snippet_html(raw) == "Scientists have discovered new evidence & verified the claim."


def test_relevance_score_computation() -> None:
    """Relevance score should reflect term coverage between claim and target snippet."""
    claim = "NASA rover finds water on Mars"
    title = "NASA Perseverance Rover Confirms Ancient Lake and Water on Mars"
    snippet = "Researchers verified the presence of water ice inside crater basins."
    score = compute_relevance_score(claim, title, snippet)
    assert 0.0 <= score <= 1.0
    assert score > 0.5

    unrelated_title = "Cooking recipe for chocolate chip cookies"
    unrelated_snippet = "Bake at 350 degrees for 12 minutes."
    low_score = compute_relevance_score(claim, unrelated_title, unrelated_snippet)
    assert low_score < score


def test_google_factcheck_provider_unavailable_without_key() -> None:
    """Google Fact Check provider should report unavailable and return [] if no key."""
    provider = GoogleFactCheckProvider(api_key=None)
    assert provider.is_available() is False


@pytest.mark.anyio
async def test_google_factcheck_provider_parses_response() -> None:
    """Provider should map Google Fact Check API JSON into standardized EvidenceItem."""
    mock_payload = {
        "claims": [
            {
                "text": "Drinking boiled garlic water cures viruses",
                "claimReview": [
                    {
                        "publisher": {"name": "Health Feedback", "site": "healthfeedback.org"},
                        "url": "https://healthfeedback.org/claimreview/garlic-water/",
                        "title": "Fact Check: Garlic water does not cure viruses",
                        "textualRating": "False",
                        "reviewDate": "2024-01-15",
                    }
                ],
            }
        ]
    }
    provider = GoogleFactCheckProvider(api_key="fake_test_key")
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: mock_payload
        mock_get.return_value = mock_resp

        results = await provider.search_evidence("garlic water viral cure", max_results=5)
        assert len(results) == 1
        ev = results[0]
        assert ev.source_name == "Health Feedback"
        assert ev.source_type == "fact_check"
        assert "healthfeedback.org" in ev.url
        assert ev.provider == "google_factcheck"


@pytest.mark.anyio
async def test_wikipedia_provider_parses_search_hits() -> None:
    """Wikipedia provider should map search API results to EvidenceItem."""
    mock_wiki_payload = {
        "query": {
            "search": [
                {
                    "title": "Mars",
                    "pageid": 146404,
                    "snippet": "Mars is the fourth planet and possesses significant <span class=\"searchmatch\">water</span> ice.",
                    "timestamp": "2024-02-01T12:00:00Z",
                }
            ]
        }
    }
    provider = WikipediaProvider()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: mock_wiki_payload
        mock_get.return_value = mock_resp

        results = await provider.search_evidence("Mars water ice", max_results=3)
        assert len(results) == 1
        assert results[0].title == "Mars"
        assert results[0].source_name == "Wikipedia"
        assert results[0].source_type == "encyclopedia"
        assert "en.wikipedia.org/wiki/Mars" in results[0].url
        assert "span class" not in results[0].snippet


@pytest.mark.anyio
async def test_evidence_retriever_deduplicates_and_isolates_failures() -> None:
    """Retriever should combine results from multiple providers, deduplicate by URL, and handle errors."""
    class WorkingProvider(BaseEvidenceProvider):
        @property
        def name(self) -> str:
            return "working_provider"

        def is_available(self) -> bool:
            return True

        async def search_evidence(self, query: str, max_results: int = 5) -> list[EvidenceItem]:
            return [
                EvidenceItem(
                    title="Article One",
                    source_name="Reuters",
                    url="https://www.reuters.com/world/news-1",
                    snippet="Official statement released today.",
                    source_type="news",
                    relevance_score=0.9,
                    provider="working_provider",
                ),
                EvidenceItem(
                    title="Article One Duplicate",
                    source_name="Reuters",
                    url="https://www.reuters.com/world/news-1?utm_source=rss",
                    snippet="Official statement duplicate snippet.",
                    source_type="news",
                    relevance_score=0.8,
                    provider="working_provider",
                ),
            ]

    class FailingProvider(BaseEvidenceProvider):
        @property
        def name(self) -> str:
            return "failing_provider"

        def is_available(self) -> bool:
            return True

        async def search_evidence(self, query: str, max_results: int = 5) -> list[EvidenceItem]:
            raise ConnectionError("External provider network timeout")

    retriever = EvidenceRetrieverService(providers=[WorkingProvider(), FailingProvider()])
    claims = [ClaimItem(claim_id="claim_1", claim_text="Official statement released today")]

    evidence_map = await retriever.retrieve_evidence_for_claims(claims)
    assert "claim_1" in evidence_map
    claim_evidence = evidence_map["claim_1"]
    # Duplicate URL should be removed, leaving exactly 1 unique item
    assert len(claim_evidence) == 1
    assert claim_evidence[0].source_name == "Reuters"
    assert claim_evidence[0].url.startswith("https://")


def test_api_claims_endpoint_validation_and_flow(client: TestClient) -> None:
    """API endpoint /api/analyze/claims should validate inputs and return structured claims + evidence."""
    # 1. Test empty input fails with 422
    res_empty = client.post("/api/analyze/claims", json={"headline": "  ", "article_text": ""})
    assert res_empty.status_code == 422

    # 2. Test valid input
    payload = {
        "headline": "James Webb Telescope spots distant galaxy formed shortly after Big Bang",
        "article_text": (
            "Astronomers published peer-reviewed findings in the Astrophysical Journal on Thursday. "
            "Spectroscopic analysis confirmed a redshift exceeding z=14."
        ),
    }
    res_valid = client.post("/api/analyze/claims", json=payload)
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert "claims" in data
    assert "evidence" in data
    assert data["claims_count"] >= 2
    assert "claim_1" in data["evidence"]
    assert isinstance(data["evidence"]["claim_1"], list)
    