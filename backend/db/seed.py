"""Seed the watchlist with 10 well-known S&P 500 tickers."""

import asyncio

from sqlalchemy import select

from config import settings  # noqa: F401 — ensures env is loaded
from db.database import async_session
from db.models import WatchlistItem

SEED_TICKERS = [
    ("AAPL", "Information Technology"),
    ("MSFT", "Information Technology"),
    ("GOOGL", "Communication Services"),
    ("AMZN", "Consumer Discretionary"),
    ("NVDA", "Information Technology"),
    ("META", "Communication Services"),
    ("TSLA", "Consumer Discretionary"),
    ("JPM", "Financials"),
    ("JNJ", "Health Care"),
    ("UNH", "Health Care"),
]


async def seed() -> None:
    """Insert seed watchlist items if they don't already exist."""
    async with async_session() as session:
        for ticker, sector in SEED_TICKERS:
            exists = await session.execute(
                select(WatchlistItem).where(WatchlistItem.ticker == ticker)
            )
            if exists.scalar_one_or_none() is None:
                session.add(WatchlistItem(ticker=ticker, sector=sector, alert_threshold="medium"))
        await session.commit()
    print(f"Seeded {len(SEED_TICKERS)} watchlist tickers.")


if __name__ == "__main__":
    asyncio.run(seed())
