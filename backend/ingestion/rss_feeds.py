"""RSS feed scraper — fetches articles from Reuters, AP, and Yahoo Finance RSS feeds."""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from config import settings

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "AP Markets", "url": "https://rsshub.app/apnews/topics/financial-markets"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/rss/"},
]


def _parse_pub_date(entry: dict) -> datetime | None:
    """Parse published date from RSS entry."""
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return None


async def fetch_rss_articles() -> list[dict]:
    """Fetch articles from all configured RSS feeds.

    Returns a list of article dicts ready for DB insertion.
    """
    articles = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for feed_info in RSS_FEEDS:
            try:
                resp = await client.get(
                    feed_info["url"],
                    headers={"User-Agent": "SP500NewsCurator/1.0"},
                )
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

                count = 0
                for entry in feed.entries:
                    url = entry.get("link", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    body = entry.get("summary", "") or entry.get("description", "")

                    articles.append({
                        "headline": entry.get("title", ""),
                        "body": body,
                        "source_url": url,
                        "published_at": _parse_pub_date(entry),
                        "source_name": feed_info["name"],
                        "raw_json": {"feed": feed_info["name"], "entry_id": entry.get("id", "")},
                    })
                    count += 1

                logger.info("RSS feed '%s' returned %d articles", feed_info["name"], count)

            except Exception:
                logger.exception("Failed to fetch RSS feed '%s'", feed_info["name"])

    logger.info("RSS total: %d unique articles", len(articles))
    return articles
