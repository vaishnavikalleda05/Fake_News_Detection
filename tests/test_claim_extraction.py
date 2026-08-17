"""Tests for claim extraction service."""

from __future__ import annotations

from backend.app.services.claim_extractor import ClaimExtractor


def test_claim_extraction_from_simple_article() -> None:
    """Extractor should break an informative article into distinct factual claims."""
    extractor = ClaimExtractor(default_max_claims=5)
    headline = "Scientists discover liquid water on Mars."
    article = (
        "NASA researchers announced the landmark finding during a press conference on Monday. "
        "The satellite images confirmed active sub-surface aquifers beneath the south pole. "
        "Further tests will determine the mineral concentration of the water."
    )
    claims = extractor.extract_claims(headline=headline, article_text=article)
    assert len(claims) >= 3
    assert claims[0].claim_id == "claim_1"
    assert "Scientists discover liquid water on Mars" in claims[0].claim_text
    assert any("NASA researchers announced" in c.claim_text for c in claims)


def test_claim_extraction_empty_or_whitespace() -> None:
    """Extractor should return empty list for empty or whitespace inputs."""
    extractor = ClaimExtractor()
    assert extractor.extract_claims("", "") == []
    assert extractor.extract_claims("   ", "   \n\t  ") == []
    assert extractor.extract_claims(None, None) == []


def test_claim_extraction_deduplication() -> None:
    """Extractor should deduplicate identical or near-identical sentences."""
    extractor = ClaimExtractor()
    headline = "Government passes new clean energy bill."
    article = (
        "Government passes new clean energy bill. "
        "The legislation was approved by the Senate on Tuesday. "
        "Government passes new clean energy bill. "
        "The legislation was approved by the Senate on Tuesday."
    )
    claims = extractor.extract_claims(headline=headline, article_text=article)
    texts = [c.claim_text.lower().strip() for c in claims]
    assert len(texts) == len(set(texts))
    assert len(claims) == 2


def test_claim_extraction_respects_max_claims_limit() -> None:
    """Extractor should strictly respect max_claims limit."""
    extractor = ClaimExtractor(default_max_claims=10)
    article = (
        "First major discovery was reported in January. "
        "Second major discovery was reported in February. "
        "Third major discovery was reported in March. "
        "Fourth major discovery was reported in April. "
        "Fifth major discovery was reported in May."
    )
    claims = extractor.extract_claims(article_text=article, max_claims=3)
    assert len(claims) == 3


def test_claim_extraction_filters_questions_and_boilerplate() -> None:
    """Extractor should ignore questions, greetings, and promotional spam."""
    extractor = ClaimExtractor()
    article = (
        "Welcome to our daily news briefing! "
        "Why did the stock market plunge this morning? "
        "Central bank officials raised benchmark interest rates by fifty basis points today. "
        "Subscribe to our newsletter to receive daily updates. "
        "Click here for more details."
    )
    claims = extractor.extract_claims(article_text=article)
    assert len(claims) == 1
    assert "Central bank officials raised" in claims[0].claim_text
    