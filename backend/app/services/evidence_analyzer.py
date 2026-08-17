"""Evidence Stance and Semantic Alignment Analyzer.

Evaluates whether a candidate evidence snippet supports, contradicts, or remains
neutral relative to an extracted factual claim.
"""

from __future__ import annotations

import re
from typing import Literal

from backend.app.models.schemas import EvidenceItem
from backend.app.providers.base_provider import tokenize

StanceType = Literal["SUPPORTS", "CONTRADICTS", "NEUTRAL"]

# Explicit debunking and contradiction signals
_CONTRADICTION_PATTERNS = re.compile(
    r"\b(false|fake|debunked|hoax|misleading|untrue|myth|disproven|disproved|"
    r"no evidence|never happened|falsely claimed|fabricated|refuted|denied that|"
    r"denies rumors?|unsubstantiated|distorted|out of context|incorrect|pants on fire)\b",
    flags=re.IGNORECASE,
)

# Explicit corroboration and affirmation signals
_SUPPORT_PATTERNS = re.compile(
    r"\b(confirmed|verified|announced|proven|proves|official findings?|"
    r"evidence shows|discovered|approved|signed into law|substantiated|"
    r"passed|agreed|concluded that|demonstrated|validated)\b",
    flags=re.IGNORECASE,
)

# Fact check explicit rating keywords
_FACT_CHECK_FALSE_RATINGS = re.compile(r"\b(false|mostly false|fake|pants on fire|misleading|scam|hoax)\b", re.I)
_FACT_CHECK_TRUE_RATINGS = re.compile(r"\b(true|mostly true|correct|verified|accurate)\b", re.I)


class EvidenceAnalyzer:
    """Analyzes semantic stance and evidence polarity relative to a claim."""

    def evaluate_stance(self, claim_text: str, evidence: EvidenceItem) -> dict[str, StanceType | float | str]:
        """Determine whether evidence supports, contradicts, or is neutral to the claim.

        Args:
            claim_text: Extracted factual claim string.
            evidence: Retrieved candidate EvidenceItem.

        Returns:
            dict containing stance ('SUPPORTS', 'CONTRADICTS', 'NEUTRAL'),
            alignment_score (0.0 to 1.0), and human-readable reason.
        """
        snippet = evidence.snippet or ""
        title = evidence.title or ""
        full_text = f"{title} {snippet}".lower()

        # If relevance score is too weak, stance is NEUTRAL
        if evidence.relevance_score < 0.18:
            return {
                "stance": "NEUTRAL",
                "alignment_score": 0.2,
                "reason": "Insufficient lexical overlap between evidence and claim.",
            }

        # 1. Fact-Check Provider specific rating analysis
        if evidence.source_type == "fact_check" or evidence.provider == "google_factcheck":
            if _FACT_CHECK_FALSE_RATINGS.search(full_text):
                return {
                    "stance": "CONTRADICTS",
                    "alignment_score": 0.95,
                    "reason": f"Accredited fact-checker ({evidence.source_name}) explicitly rated this claim as false/misleading.",
                }
            if _FACT_CHECK_TRUE_RATINGS.search(full_text):
                return {
                    "stance": "SUPPORTS",
                    "alignment_score": 0.92,
                    "reason": f"Accredited fact-checker ({evidence.source_name}) verified this claim as true/accurate.",
                }

        # 2. Check for refutation / debunking language
        has_contradiction = bool(_CONTRADICTION_PATTERNS.search(full_text))
        has_support = bool(_SUPPORT_PATTERNS.search(full_text))

        if has_contradiction and not has_support:
            return {
                "stance": "CONTRADICTS",
                "alignment_score": 0.88,
                "reason": f"Source text from {evidence.source_name} contains explicit refutation or debunking statements.",
            }

        if has_support and not has_contradiction:
            # Check if key subject tokens from claim appear in evidence
            claim_tokens = set(tokenize(claim_text))
            evidence_tokens = set(tokenize(full_text))
            overlap_ratio = len(claim_tokens.intersection(evidence_tokens)) / max(len(claim_tokens), 1)

            if overlap_ratio >= 0.40:
                return {
                    "stance": "SUPPORTS",
                    "alignment_score": min(0.90, 0.5 + (overlap_ratio * 0.45)),
                    "reason": f"Source text from {evidence.source_name} corroborates key factual assertions in the claim.",
                }

        # 3. High-relevance news/official reporting without contradiction
        if evidence.source_type in ("official", "research", "news") and evidence.relevance_score >= 0.60:
            return {
                "stance": "SUPPORTS",
                "alignment_score": min(0.85, evidence.relevance_score),
                "reason": f"High-relevance reporting by reputable source ({evidence.source_name}) matches the subject.",
            }

        return {
            "stance": "NEUTRAL",
            "alignment_score": 0.4,
            "reason": "Evidence provides general context but does not explicitly verify or refute the claim.",
        }


# Singleton instance
evidence_analyzer = EvidenceAnalyzer()