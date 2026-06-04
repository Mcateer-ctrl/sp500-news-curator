"""Article endpoints — list, filter, and retrieve articles with sentiment scores."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_session
from db.models import Article, ScoredArticle

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleResponse(BaseModel):
    """Serialized article with optional scoring data."""
    id: str
    headline: str
    body: str
    source_url: str
    published_at: Optional[datetime] = None
    source_name: str
    created_at: datetime
    # Scoring fields (None if not scored)
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    impact: Optional[str] = None
    impact_reason: Optional[str] = None
    time_horizon: Optional[str] = None
    summary: Optional[str] = None
    affected_tickers: Optional[list[str]] = None
    affected_sectors: Optional[list[str]] = None
    scored_by: Optional[str] = None
    llm_provider: Optional[str] = None

    model_config = {"from_attributes": True}


def _serialize_article(article: Article) -> dict:
    """Convert an Article + optional ScoredArticle to a response dict."""
    data = {
        "id": str(article.id),
        "headline": article.headline,
        "body": article.body,
        "source_url": article.source_url,
        "published_at": article.published_at,
        "source_name": article.source_name,
        "created_at": article.created_at,
    }
    sa = article.scored_article
    if sa:
        data.update({
            "sentiment": sa.sentiment,
            "confidence": sa.confidence,
            "impact": sa.impact,
            "impact_reason": sa.impact_reason,
            "time_horizon": sa.time_horizon,
            "summary": sa.summary,
            "affected_tickers": sa.affected_tickers,
            "affected_sectors": sa.affected_sectors,
            "scored_by": sa.scored_by,
            "llm_provider": sa.llm_provider,
        })
    return data


@router.get("")
async def list_articles(
    ticker: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    impact: Optional[str] = Query(None),
    hours: int = Query(24, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List articles with optional filters."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = (
        select(Article)
        .options(selectinload(Article.scored_article))
        .where(Article.created_at >= cutoff)
        .order_by(Article.published_at.desc().nullslast())
    )

    if ticker:
        query = query.join(ScoredArticle).where(
            ScoredArticle.affected_tickers.any(ticker.upper())
        )
    if sector:
        query = query.join(ScoredArticle, isouter=False).where(
            ScoredArticle.affected_sectors.any(sector)
        )
    if sentiment:
        query = query.join(ScoredArticle, isouter=False).where(
            ScoredArticle.sentiment == sentiment
        )
    if impact:
        query = query.join(ScoredArticle, isouter=False).where(
            ScoredArticle.impact == impact
        )

    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    articles = result.scalars().unique().all()

    return {"articles": [_serialize_article(a) for a in articles], "count": len(articles)}


@router.get("/{article_id}")
async def get_article(
    article_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get full article detail including scoring breakdown."""
    try:
        uid = uuid.UUID(article_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid article ID format")

    result = await session.execute(
        select(Article)
        .options(selectinload(Article.scored_article))
        .where(Article.id == uid)
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return _serialize_article(article)
