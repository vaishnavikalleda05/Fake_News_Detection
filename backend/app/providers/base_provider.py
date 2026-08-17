"""Base provider abstract class and evidence utility functions."""

from __future__ import annotations

import html
import re
from abc import ABC, abstractmethod
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from backend.app.models.schemas import EvidenceItem

# Basic English stopwords to filter during relevance scoring
_STOPWORDS = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't",
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll",
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's",
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
    "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't",
    "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
})


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def compute_relevance_score(claim_text: str, title: str, snippet: str) -> float:
    """Compute a normalized relevance score between 0.0 and 1.0 based on lexical overlap.

    Evaluates keyword coverage between the claim and the retrieved title/snippet.
    """
    claim_tokens = [w for w in tokenize(claim_text) if w not in _STOPWORDS and len(w) > 2]
    if not claim_tokens:
        return 0.5

    claim_set = set(claim_tokens)
    target_tokens = set(tokenize(f"{title} {snippet}"))

    # Word coverage: fraction of claim keywords found in target
    intersection = claim_set.intersection(target_tokens)
    coverage = len(intersection) / len(claim_set)

    # Title match bonus: if title contains keywords
    title_tokens = set(tokenize(title))
    title_overlap = len(claim_set.intersection(title_tokens)) / len(claim_set)

    # Combined score
    score = (coverage * 0.7) + (title_overlap * 0.3)
    return round(min(max(score, 0.0), 1.0), 3)


def clean_snippet_html(raw_html: str) -> str:
    """Strip HTML tags and properly unescape entities from snippet text."""
    if not raw_html:
        return ""
    text = html.unescape(raw_html)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_url(raw_url: str) -> str:
    """Normalize URL by stripping tracking queries and standardizing scheme/netloc."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        if not parsed.scheme or not parsed.netloc:
            return raw_url

        # Remove UTM and tracking query parameters
        filtered_queries = [
            (k, v)
            for k, v in parse_qsl(parsed.query)
            if not k.lower().startswith(("utm_", "fbclid", "gclid", "ref", "source"))
        ]
        new_query = urlencode(filtered_queries)
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") if parsed.path != "/" else "/",
            parsed.params,
            new_query,
            "",  # strip fragment
        ))
        return normalized
    except Exception:
        return raw_url


class BaseEvidenceProvider(ABC):
    """Abstract Base Class for all external evidence retrieval providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name of this provider."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available for querying."""

    @abstractmethod
    async def search_evidence(self, query: str, max_results: int = 5) -> list[EvidenceItem]:
        """Search and retrieve a list of normalized evidence items for a given claim query.

        Args:
            query: Claim or search statement.
            max_results: Maximum number of evidence candidate items to return.

        Returns:
            list of EvidenceItem instances.
        """