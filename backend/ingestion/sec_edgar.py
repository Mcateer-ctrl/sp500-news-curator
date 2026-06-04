"""SEC EDGAR RSS client — polls for 8-K and 10-Q filings from S&P 500 companies."""

import logging
from datetime import datetime

import feedparser
import httpx

logger = logging.getLogger(__name__)

EDGAR_FEED_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&type=8-K&dateb=&owner=include&count=20&search_text=&output=atom"
)

EDGAR_10Q_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcurrent&type=10-Q&dateb=&owner=include&count=20&search_text=&output=atom"
)


def _parse_pub_date(entry: dict) -> datetime | None:
    """Parse published date from EDGAR Atom entry."""
    raw = entry.get("updated") or entry.get("published")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


async def fetch_sec_filings() -> list[dict]:
    """Fetch recent SEC EDGAR 8-K and 10-Q filings.

    Returns a list of article dicts ready for DB insertion.
    """
    articles = []
    seen_urls: set[str] = set()

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for feed_url, filing_type in [(EDGAR_FEED_URL, "8-K"), (EDGAR_10Q_URL, "10-Q")]:
            try:
                resp = await client.get(
                    feed_url,
                    headers={
                        "User-Agent": "SP500NewsCurator admin@example.com",
                        "Accept": "application/atom+xml",
                    },
                )
                resp.raise_for_status()
                feed = feedparser.parse(resp.text)

                count = 0
                for entry in feed.entries:
                    url = entry.get("link", "")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    articles.append({
                        "headline": entry.get("title", f"SEC {filing_type} Filing"),
                        "body": entry.get("summary", ""),
                        "source_url": url,
                        "published_at": _parse_pub_date(entry),
                        "source_name": f"SEC EDGAR ({filing_type})",
                        "raw_json": {"filing_type": filing_type, "entry_id": entry.get("id", "")},
                    })
                    count += 1

                logger.info("SEC EDGAR %s: %d filings", filing_type, count)

            except Exception:
                logger.exception("Failed to fetch SEC EDGAR %s feed", filing_type)

    logger.info("SEC EDGAR total: %d filings", len(articles))
    return articles
