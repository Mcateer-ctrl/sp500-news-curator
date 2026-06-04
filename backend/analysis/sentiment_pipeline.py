"""Sentiment pipeline — orchestrates FinBERT pre-filter and LLM deep analysis."""

import asyncio
import logging
from typing import Optional

from config import settings
from analysis.finbert import run_finbert, FinBertResult
from analysis.llm_client import score_with_llm, LLMSentimentResult
from analysis.ticker_mapper import extract_tickers
from db.models import Article, ScoredArticle

logger = logging.getLogger(__name__)

# Semaphore to limit concurrent LLM calls (avoid rate limiting)
# Initialized lazily on first use
_llm_semaphore: Optional[asyncio.Semaphore] = None


def _get_llm_semaphore() -> asyncio.Semaphore:
    """Get or create the LLM semaphore with configurable concurrency."""
    global _llm_semaphore
    if _llm_semaphore is None:
        max_concurrent = settings.max_concurrent_llm_calls
        _llm_semaphore = asyncio.Semaphore(max_concurrent)
        logger.info("Initialized LLM semaphore with max_concurrent=%d", max_concurrent)
    return _llm_semaphore


def _finbert_to_sentiment(label: str) -> str:
    """Map FinBERT label to our sentiment vocabulary."""
    mapping = {"positive": "bullish", "negative": "bearish", "neutral": "neutral"}
    return mapping.get(label, "neutral")


def _build_scored_from_finbert(
    article: Article, result: FinBertResult, source: str
) -> ScoredArticle:
    """Build a ScoredArticle from a FinBERT result."""
    ticker_info = extract_tickers(f"{article.headline} {article.body}")
    tickers = [t["ticker"] for t in ticker_info]
    sectors = list({t["sector"] for t in ticker_info})

    confidence = max(result.positive, result.negative, result.neutral)
    return ScoredArticle(
        article_id=article.id,
        sentiment=_finbert_to_sentiment(result.label),
        confidence=confidence,
        impact="low",
        impact_reason="Scored by FinBERT headline analysis only",
        time_horizon="short_term",
        summary="",
        affected_tickers=tickers,
        affected_sectors=sectors,
        scored_by=source,
        llm_provider=None,
    )


def _build_scored_from_llm(
    article: Article, result: LLMSentimentResult, llm_provider: str
) -> ScoredArticle:
    """Build a ScoredArticle from an LLM result."""
    return ScoredArticle(
        article_id=article.id,
        sentiment=result.sentiment,
        confidence=result.confidence,
        impact=result.impact,
        impact_reason=result.impact_reason,
        time_horizon=result.time_horizon,
        summary=result.summary,
        affected_tickers=result.affected_tickers,
        affected_sectors=result.affected_sectors,
        scored_by="llm",
        llm_provider=llm_provider,
    )


async def process_article(article: Article) -> ScoredArticle:
    """Run the two-stage sentiment pipeline on a single article.

    Stage 1: FinBERT on headline (fast, free, local).
    Stage 2: LLM deep analysis if FinBERT isn't confidently neutral.
    """
    # Stage 1: FinBERT
    finbert_result = await run_finbert(article.headline)
    logger.info(
        "FinBERT scored article %s: label=%s neutral=%.3f",
        article.id, finbert_result.label, finbert_result.neutral,
    )

    # Stage 2: Skip LLM if FinBERT is very confident it's neutral
    if finbert_result.neutral > settings.finbert_neutral_threshold:
        return _build_scored_from_finbert(article, finbert_result, source="finbert")

    # Stage 3: LLM deep analysis
    body_truncated = (article.body or "")[:settings.max_article_body_chars]
    async with _get_llm_semaphore():
        llm_result = await score_with_llm(article.headline, body_truncated)

    if llm_result is None:
        logger.warning("LLM failed for article %s — falling back to FinBERT", article.id)
        return _build_scored_from_finbert(article, finbert_result, source="finbert_fallback")

    return _build_scored_from_llm(article, llm_result, llm_provider=settings.llm_provider)


async def process_batch(articles: list[Article]) -> list[ScoredArticle]:
    """Process a batch of articles concurrently (max 5 parallel LLM calls via semaphore)."""
    tasks = [process_article(article) for article in articles]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    scored = []
    for article, result in zip(articles, results):
        if isinstance(result, Exception):
            logger.exception("Failed to process article %s: %s", article.id, result)
        else:
            scored.append(result)
    return scored
