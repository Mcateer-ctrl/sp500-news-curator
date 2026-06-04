"""Scheduler — APScheduler jobs for periodic ingestion and scoring."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from config import settings
from db.database import async_session
from db.models import Article, ScoredArticle
from ingestion.news_api import fetch_newsapi_articles
from ingestion.rss_feeds import fetch_rss_articles
from ingestion.sec_edgar import fetch_sec_filings
from analysis.sentiment_pipeline import process_batch

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _store_articles(raw_articles: list[dict]) -> list[Article]:
    """Store articles in the database, skipping duplicates. Returns newly inserted articles."""
    new_articles = []
    async with async_session() as session:
        for item in raw_articles:
            exists = await session.execute(
                select(Article).where(Article.source_url == item["source_url"])
            )
            if exists.scalar_one_or_none() is not None:
                continue

            article = Article(
                headline=item["headline"],
                body=item["body"],
                source_url=item["source_url"],
                published_at=item.get("published_at"),
                source_name=item.get("source_name", ""),
                raw_json=item.get("raw_json"),
            )
            session.add(article)
            new_articles.append(article)

        if new_articles:
            await session.commit()
            # Refresh to get generated IDs
            for a in new_articles:
                await session.refresh(a)

    return new_articles


async def ingest_all_sources() -> dict:
    """Fetch articles from all sources and store new ones. Returns ingestion stats."""
    logger.info("Starting ingestion from all sources...")
    all_raw: list[dict] = []

    # Fetch from all sources (catch each independently)
    for fetch_fn, name in [
        (fetch_newsapi_articles, "NewsAPI"),
        (fetch_rss_articles, "RSS"),
        (fetch_sec_filings, "SEC EDGAR"),
    ]:
        try:
            articles = await fetch_fn()
            all_raw.extend(articles)
            logger.info("Fetched %d articles from %s", len(articles), name)
        except Exception:
            logger.exception("Failed to fetch from %s", name)

    # Deduplicate by URL
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in all_raw:
        if item["source_url"] not in seen:
            seen.add(item["source_url"])
            deduped.append(item)

    new_articles = await _store_articles(deduped)
    logger.info("Ingestion complete: %d fetched, %d new, %d skipped",
                len(deduped), len(new_articles), len(deduped) - len(new_articles))

    # Score new articles
    if new_articles:
        scored = await process_batch(new_articles)
        async with async_session() as session:
            for sa_obj in scored:
                session.add(sa_obj)
            await session.commit()
        logger.info("Scored %d/%d new articles", len(scored), len(new_articles))

    return {"fetched": len(deduped), "new": len(new_articles), "scored": len(new_articles)}


async def process_unscored_articles() -> int:
    """Find and score any articles that don't have a ScoredArticle yet."""
    async with async_session() as session:
        result = await session.execute(
            select(Article).where(
                ~Article.id.in_(select(ScoredArticle.article_id))
            ).limit(50)
        )
        unscored = list(result.scalars().all())

    if not unscored:
        return 0

    logger.info("Found %d unscored articles — processing", len(unscored))
    scored = await process_batch(unscored)

    async with async_session() as session:
        for sa_obj in scored:
            session.add(sa_obj)
        await session.commit()

    logger.info("Scored %d unscored articles", len(scored))
    return len(scored)


def start_scheduler() -> None:
    """Register and start the APScheduler jobs."""
    scheduler.add_job(
        ingest_all_sources,
        "interval",
        minutes=settings.ingest_interval_minutes,
        id="ingest_all_sources",
        replace_existing=True,
    )
    scheduler.add_job(
        process_unscored_articles,
        "interval",
        minutes=5,
        id="process_unscored_articles",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: ingestion every %d min, unscored processing every 5 min",
        settings.ingest_interval_minutes,
    )


def stop_scheduler() -> None:
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
