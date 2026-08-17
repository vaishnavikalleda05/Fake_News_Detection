"""Factual Claim Extraction Service.

Identifies verifiable factual statements from news headlines and article text
using heuristic sentence segmentation, factual indicators, and deduplication.
"""

from __future__ import annotations

import re
from typing import Final

from backend.app.config import settings
from backend.app.models.schemas import ClaimItem

# Common abbreviations to prevent false sentence splitting
_ABBREVIATIONS: Final[tuple[str, ...]] = (
    "u.s.", "u.k.", "u.n.", "e.u.", "dr.", "mr.", "mrs.", "ms.", "prof.", "gen.",
    "rep.", "sen.", "gov.", "pres.", "dept.", "inc.", "corp.", "ltd.", "co.",
    "jan.", "feb.", "mar.", "apr.", "jun.", "jul.", "aug.", "sep.", "sept.", "oct.", "nov.", "dec.",
    "vs.", "approx.", "est.", "e.g.", "i.e.", "a.m.", "p.m."
)

# Boilerplate patterns to discard
_BOILERPLATE_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(click here|subscribe|newsletter|follow us|share this|all rights reserved|photo by|image credit|"
    r"advertisement|sign up|read more|terms of service|privacy policy|comment below)\b",
    flags=re.IGNORECASE,
)

# Factuality indicator keywords (verbs/terms suggesting testable assertions)
_FACTUAL_INDICATORS_RE: Final[re.Pattern[str]] = re.compile(
    r"\b(announced|stated|reported|discovered|found|confirmed|signed|passed|voted|approved|"
    r"banned|killed|injured|increased|decreased|signed|launched|declared|tested|revealed|"
    r"published|concluded|conducted|developed|manufactured|occurred|happened|showed|claims?)\b",
    flags=re.IGNORECASE,
)

_NUMERIC_FACT_RE: Final[re.Pattern[str]] = re.compile(r"\b(\d+([.,]\d+)?%?|\$\d+|\d{4})\b")


def _normalize_for_dedupe(text: str) -> str:
    """Normalize text to a clean token sequence for similarity comparison."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _is_boilerplate_or_opinion(sentence: str) -> bool:
    """Return True if sentence looks like boilerplate, navigation, or conversational noise."""
    if _BOILERPLATE_RE.search(sentence):
        return True
    # Filter out questions (not factual claims)
    if sentence.endswith("?"):
        return True
    # Filter out greetings or short conversational banter
    lower = sentence.lower()
    if lower.startswith(("hello", "welcome", "good morning", "good evening", "hi there", "thanks for reading")):
        return True
    return False


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences while protecting common abbreviations and decimals."""
    if not text or not text.strip():
        return []

    # Normalize newlines and whitespace
    cleaned = re.sub(r"\r\n|\r|\n", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Split using punctuation boundaries followed by whitespace and capital letter
    raw_splits = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", cleaned)
    
    sentences: list[str] = []
    buffer = ""

    for chunk in raw_splits:
        candidate = f"{buffer} {chunk}".strip() if buffer else chunk.strip()
        # Check if the sentence ends in a known abbreviation
        last_word = candidate.split()[-1].lower() if candidate.split() else ""
        if any(last_word == abbr or last_word.endswith(abbr) for abbr in _ABBREVIATIONS):
            buffer = candidate
            continue

        buffer = ""
        if candidate:
            sentences.append(candidate)

    if buffer:
        sentences.append(buffer)

    return sentences


def _score_sentence_factuality(sentence: str) -> float:
    """Score the verifiability and informational density of a sentence."""
    score = 0.0
    words = sentence.split()
    word_count = len(words)

    # Ideal length for a factual statement is between 6 and 40 words
    if 6 <= word_count <= 40:
        score += 1.0
    elif word_count > 40:
        score += 0.5

    # Check for reporting/assertion verbs
    if _FACTUAL_INDICATORS_RE.search(sentence):
        score += 1.5

    # Check for numeric data, statistics, years
    if _NUMERIC_FACT_RE.search(sentence):
        score += 1.0

    # Check for capitalized proper entities (potential named entities)
    proper_nouns = [w for w in words[1:] if w and w[0].isupper() and w.isalpha()]
    if proper_nouns:
        score += min(len(proper_nouns) * 0.3, 1.2)

    return score


class ClaimExtractor:
    """Extracts factual, verifiable claims from news content."""

    def __init__(self, default_max_claims: int | None = None) -> None:
        self.default_max_claims = default_max_claims or settings.MAX_CLAIMS_PER_ANALYSIS

    def extract_claims(
        self,
        headline: str | None = None,
        article_text: str | None = None,
        max_claims: int | None = None,
    ) -> list[ClaimItem]:
        """Extract a structured list of discrete factual claims.

        Args:
            headline: Optional headline string.
            article_text: Optional article body text.
            max_claims: Maximum number of claims to extract.

        Returns:
            list of ClaimItem instances.
        """
        limit = max_claims or self.default_max_claims
        seen_dedupe_keys: set[str] = set()
        candidate_claims: list[tuple[str, float, bool]] = []  # (text, score, is_headline)

        # 1. Process Headline if provided
        if headline and headline.strip():
            clean_hl = re.sub(r"\s+", " ", headline).strip()
            if len(clean_hl) >= 15 and len(clean_hl.split()) >= 3 and not _is_boilerplate_or_opinion(clean_hl):
                hl_key = _normalize_for_dedupe(clean_hl)
                seen_dedupe_keys.add(hl_key)
                candidate_claims.append((clean_hl, 10.0, True))  # High priority for headline

        # 2. Process Article Body
        if article_text and article_text.strip():
            sentences = _split_into_sentences(article_text)
            for sent in sentences:
                sent_clean = re.sub(r"\s+", " ", sent).strip()
                # Discard too short or noisy sentences
                if len(sent_clean) < 20 or len(sent_clean.split()) < 4:
                    continue
                if _is_boilerplate_or_opinion(sent_clean):
                    continue

                dedupe_key = _normalize_for_dedupe(sent_clean)
                if dedupe_key in seen_dedupe_keys:
                    continue

                # Check if this sentence is substantially substring of an already added claim
                if any(dedupe_key in existing or existing in dedupe_key for existing in seen_dedupe_keys):
                    continue

                seen_dedupe_keys.add(dedupe_key)
                score = _score_sentence_factuality(sent_clean)
                candidate_claims.append((sent_clean, score, False))

        if not candidate_claims:
            return []

        # Headline always stays first if present, then sort remaining by factuality score
        final_claims: list[str] = []
        headline_candidates = [c[0] for c in candidate_claims if c[2]]
        body_candidates = [c for c in candidate_claims if not c[2]]

        # Sort body candidates by score descending
        body_candidates.sort(key=lambda item: item[1], reverse=True)

        if headline_candidates:
            final_claims.append(headline_candidates[0])

        for text, _, _ in body_candidates:
            if len(final_claims) >= limit:
                break
            final_claims.append(text)

        return [
            ClaimItem(claim_id=f"claim_{idx + 1}", claim_text=text)
            for idx, text in enumerate(final_claims)
        ]


# Singleton instance
claim_extractor = ClaimExtractor()
