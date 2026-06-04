"""NewsAPI.org client — fetches financial news articles."""

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

NEWSAPI_BASE = "https://newsapi.org/v2/everything"
QUERIES = ["S&P 500", "stock market", "earnings", "Federal Reserve"]


async def fetch_newsapi_articles() -> list[dict]:
    """Fetch articles from NewsAPI.org for financial queries.

    Returns a list of article dicts ready for DB insertion.
    Each dict has: headline, body, source_url, published_at, source_name, raw_json.
    """
    if not settings.newsapi_key:
        logger.warning("NEWSAPI_KEY not set — skipping NewsAPI ingestion")
        return []

    articles = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for query in QUERIES:
            try:
                resp = await client.get(
                    NEWSAPI_BASE,
                    params={
                        "q": query,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": 25,
                        "apiKey": settings.newsapi_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("articles", []):
                    url = item.get("url", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    published_at = None
                    if item.get("publishedAt"):
                        try:
                            published_at = datetime.fromisoformat(
                                item["publishedAt"].replace("Z", "+00:00")
                            )
                        except (ValueError, TypeError):
                            pass

                    articles.append({
                        "headline": item.get("title", ""),
                        "body": item.get("content") or item.get("description") or "",
                        "source_url": url,
                        "published_at": published_at,
                        "source_name": item.get("source", {}).get("name", "NewsAPI"),
                        "raw_json": item,
                    })

                logger.info("NewsAPI query='%s' returned %d articles", query, len(data.get("articles", [])))

            except Exception:
                logger.exception("Failed to fetch NewsAPI articles for query='%s'", query)

    logger.info("NewsAPI total: %d unique articles", len(articles))
    return articles
