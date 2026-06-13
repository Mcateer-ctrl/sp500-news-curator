import logging
from datetime import datetime, timezone, timedelta, date

from sqlalchemy import select, func, and_

from db.database import async_session
from db.models import ScoredArticle, SentimentHistory

logger = logging.getLogger(__name__)


async def aggregate_daily_sentiment(target_date: date | None = None) -> int:
    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    start_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(target_date, datetime.max.time(), tzinfo=timezone.utc)

    async with async_session() as session:
        result = await session.execute(
            select(
                func.unnest(ScoredArticle.affected_tickers).label("ticker"),
                func.count().label("total"),
                func.count().filter(ScoredArticle.sentiment == "bullish").label("bullish"),
                func.count().filter(ScoredArticle.sentiment == "bearish").label("bearish"),
                func.count().filter(ScoredArticle.sentiment == "neutral").label("neutral"),
                func.avg(ScoredArticle.confidence).label("avg_conf"),
            )
            .where(
                and_(
                    ScoredArticle.scored_at >= start_dt,
                    ScoredArticle.scored_at < end_dt,
                )
            )
            .group_by(func.unnest(ScoredArticle.affected_tickers))
        )
        rows = result.all()

    inserted = 0
    async with async_session() as session:
        for row in rows:
            total = row.total or 0
            if total == 0:
                continue
            bullish = row.bullish or 0
            bearish = row.bearish or 0
            neutral = row.neutral or 0
            avg_conf = float(row.avg_conf or 0)
            composite = round((bullish - bearish) / total, 4)

            existing = await session.execute(
                select(SentimentHistory).where(
                    SentimentHistory.ticker == row.ticker,
                    SentimentHistory.date == start_dt,
                )
            )
            if existing.scalar_one_or_none():
                continue

            sh = SentimentHistory(
                ticker=row.ticker,
                date=start_dt,
                bullish_count=bullish,
                bearish_count=bearish,
                neutral_count=neutral,
                total_articles=total,
                avg_confidence=avg_conf,
                composite_score=composite,
            )
            session.add(sh)
            inserted += 1
        if inserted:
            await session.commit()

    logger.info("Aggregated %d ticker-days for %s", inserted, target_date)
    return inserted
