"""Source Quality Scoring Service.

Computes transparent source credibility scores (0-100) based on domain authority,
source type categorization, peer-review standards, and metadata completeness.
"""

from __future__ import annotations

from urllib.parse import urlparse

_TOP_AUTHORITY_DOMAINS = frozenset({
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "nytimes.com",
    "washingtonpost.com", "wsj.com", "theguardian.com", "bloomberg.com",
    "npr.org", "nature.com", "science.org", "sciencedirect.com", "ncbi.nlm.nih.gov",
    "snopes.com", "politifact.com", "factcheck.org", "fullfact.org",
    "who.int", "cdc.gov", "nasa.gov", "un.org", "nih.gov", "whitehouse.gov",
})

_USER_GENERATED_DOMAINS = frozenset({
    "facebook.com", "twitter.com", "x.com", "tiktok.com", "reddit.com",
    "blogspot.com", "wordpress.com", "medium.com", "tumblr.com",
})


class SourceScoringService:
    """Evaluates and scores publisher quality and domain authority on a 0-100 scale."""

    def score_source(
        self,
        source_name: str,
        url: str,
        source_type: str,
        publication_date: str | None = None,
    ) -> dict[str, int | str]:
        """Compute an explainable source quality score between 0 and 100.

        Args:
            source_name: Name of publisher.
            url: Canonical URL.
            source_type: Categorized type (official, fact_check, research, news, encyclopedia, other).
            publication_date: Optional publication timestamp.

        Returns:
            dict containing source_quality_score, source_type, and transparent rationale.
        """
        reasons: list[str] = []
        domain = ""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
        except Exception:
            domain = ""

        # 1. Base Score by Source Type
        if source_type == "official":
            score = 92
            reasons.append("Official government or international organizational source (+92)")
        elif source_type == "fact_check":
            score = 92
            reasons.append("Accredited professional fact-checking publication (+92)")
        elif source_type == "research":
            score = 88
            reasons.append("Peer-reviewed research repository or academic journal (+88)")
        elif source_type == "news":
            score = 78
            reasons.append("Established journalistic news publication (+78)")
        elif source_type == "encyclopedia":
            score = 70
            reasons.append("Open encyclopedia knowledge base (+70)")
        else:
            score = 45
            reasons.append("General web/unclassified source (+45)")

        # 2. Domain Authority Heuristics
        if domain:
            # TLD bonuses
            if domain.endswith((".gov", ".mil", ".int", ".edu")):
                score += 6
                reasons.append("High-trust top-level domain (.gov/.edu/.int) (+6)")

            # Top news and fact check outlets
            if any(domain == top or domain.endswith(f".{top}") for top in _TOP_AUTHORITY_DOMAINS):
                score += 5
                reasons.append(f"Recognized high-authority global publisher '{domain}' (+5)")

            # User-generated / social content penalty
            if any(domain == u or domain.endswith(f".{u}") for u in _USER_GENERATED_DOMAINS):
                score -= 25
                reasons.append("User-generated / blog platform with unverified editorial oversight (-25)")

        # 3. Metadata Completeness
        if publication_date and publication_date.strip():
            score += 3
            reasons.append("Verified publication timestamp available (+3)")

        final_score = min(max(score, 10), 100)
        return {
            "source_quality_score": final_score,
            "source_type": source_type,
            "reason": "; ".join(reasons),
        }


# Singleton instance
source_scoring_service = SourceScoringService()