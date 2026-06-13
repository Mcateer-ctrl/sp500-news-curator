"""Sentiment endpoints — per-ticker trends and sector summaries."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, and_, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Article, ScoredArticle, SentimentHistory

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/ticker/{ticker}")
async def sentiment_by_ticker(
    ticker: str,
    hours: int = Query(168, ge=1),
    session: AsyncSession = Depends(get_session),
):
    """Get sentiment trend for a specific ticker over the given time window.

    Returns hourly buckets with bullish/bearish/neutral counts and
    the latest articles mentioning this ticker.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    ticker_upper = ticker.upper()

    # Hourly sentiment trend
    trend_query = (
        select(
            func.date_trunc("hour", ScoredArticle.scored_at).label("hour"),
            func.count().filter(ScoredArticle.sentiment == "bullish").label("bullish_count"),
            func.count().filter(ScoredArticle.sentiment == "bearish").label("bearish_count"),
            func.count().filter(ScoredArticle.sentiment == "neutral").label("neutral_count"),
            func.avg(ScoredArticle.confidence).label("avg_confidence"),
        )
        .where(
            and_(
                ScoredArticle.scored_at >= cutoff,
                ScoredArticle.affected_tickers.any(ticker_upper),
            )
        )
        .group_by(func.date_trunc("hour", ScoredArticle.scored_at))
        .order_by(func.date_trunc("hour", ScoredArticle.scored_at))
    )
    trend_result = await session.execute(trend_query)
    trend_rows = trend_result.all()

    sentiment_trend = []
    for row in trend_rows:
        sentiment_trend.append({
            "hour": row.hour.isoformat() if row.hour else None,
            "bullish_count": row.bullish_count or 0,
            "bearish_count": row.bearish_count or 0,
            "neutral_count": row.neutral_count or 0,
            "avg_confidence": round(float(row.avg_confidence or 0), 3),
        })

    # Latest articles for this ticker
    latest_query = (
        select(Article)
        .join(ScoredArticle)
        .where(
            and_(
                ScoredArticle.scored_at >= cutoff,
                ScoredArticle.affected_tickers.any(ticker_upper),
            )
        )
        .order_by(Article.published_at.desc().nullslast())
        .limit(20)
    )
    latest_result = await session.execute(latest_query)
    latest_articles = latest_result.scalars().all()

    return {
        "ticker": ticker_upper,
        "sentiment_trend": sentiment_trend,
        "latest_articles": [
            {
                "id": str(a.id),
                "headline": a.headline,
                "source_name": a.source_name,
                "published_at": a.published_at,
            }
            for a in latest_articles
        ],
    }


@router.get("/sectors")
async def sentiment_by_sectors(
    hours: int = Query(24, ge=1),
    session: AsyncSession = Depends(get_session),
):
    """Get current sentiment summary grouped by GICS sector."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(
            func.unnest(ScoredArticle.affected_sectors).label("sector"),
            func.count().label("total"),
            func.count().filter(ScoredArticle.sentiment == "bullish").label("bullish"),
            func.count().filter(ScoredArticle.sentiment == "bearish").label("bearish"),
            func.count().filter(ScoredArticle.sentiment == "neutral").label("neutral"),
            func.avg(ScoredArticle.confidence).label("avg_confidence"),
        )
        .where(ScoredArticle.scored_at >= cutoff)
        .group_by(func.unnest(ScoredArticle.affected_sectors))
        .order_by(func.count().desc())
    )
    result = await session.execute(query)
    rows = result.all()

    return {
        "sectors": [
            {
                "sector": row.sector,
                "total": row.total,
                "bullish": row.bullish or 0,
                "bearish": row.bearish or 0,
                "neutral": row.neutral or 0,
                "avg_confidence": round(float(row.avg_confidence or 0), 3),
            }
            for row in rows
        ]
    }

@router.get("/history/{ticker}")
async def sentiment_history(
    ticker: str,
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = (
        select(SentimentHistory)
        .where(
            and_(
                SentimentHistory.ticker == ticker.upper(),
                SentimentHistory.date >= cutoff,
            )
        )
        .order_by(SentimentHistory.date)
    )
    result = await session.execute(query)
    rows = result.scalars().all()

    return {
        "ticker": ticker.upper(),
        "history": [
            {
                "date": r.date.isoformat(),
                "composite_score": r.composite_score,
                "bullish_count": r.bullish_count,
                "bearish_count": r.bearish_count,
                "neutral_count": r.neutral_count,
                "total_articles": r.total_articles,
                "avg_confidence": r.avg_confidence,
            }
            for r in rows
        ],
    }
