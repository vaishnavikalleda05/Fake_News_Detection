"""Article URL fetching and readable-text extraction."""

from __future__ import annotations

import httpx
import trafilatura
from fastapi import HTTPException


class ArticleURLService:
    """Fetch a webpage and extract its readable article content."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    async def extract_article(
        self,
        url: str,
    ) -> dict[str, str]:
        """Fetch URL and return extracted title and article text."""

        url = url.strip()

        if not url:
            raise HTTPException(
                status_code=422,
                detail="Article URL is required.",
            )

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):
            raise HTTPException(
                status_code=422,
                detail="Please provide a valid HTTP or HTTPS URL.",
            )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 "
                        "(Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 "
                        "(KHTML, like Gecko) "
                        "Chrome/131.0 Safari/537.36"
                    )
                },
            ) as client:

                response = await client.get(url)

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="The article website took too long to respond.",
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Unable to access the article URL. "
                    f"Website returned HTTP {exc.response.status_code}."
                ),
            ) from exc

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=422,
                detail="Unable to access the provided article URL.",
            ) from exc

        html = response.text

        extracted_text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            include_links=False,
            favor_precision=True,
        )

        if not extracted_text:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Could not extract readable article text "
                    "from this webpage."
                ),
            )

        metadata = trafilatura.extract_metadata(html)

        title = ""

        if metadata and metadata.title:
            title = metadata.title.strip()

        if not title:
            title = self._extract_title(html)

        return {
            "headline": title,
            "article_text": extracted_text.strip(),
            "source_url": url,
        }

    @staticmethod
    def _extract_title(html: str) -> str:
        """Fallback title extraction."""

        import re

        match = re.search(
            r"<title[^>]*>(.*?)</title>",
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        if match:
            return re.sub(
                r"\s+",
                " ",
                match.group(1),
            ).strip()

        return ""


article_url_service = ArticleURLService()