"""Watchlist CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import WatchlistItem

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistCreate(BaseModel):
    """Request body for adding a ticker to the watchlist."""
    ticker: str
    alert_threshold: str = "medium"


class WatchlistResponse(BaseModel):
    """Serialized watchlist item."""
    id: str
    ticker: str
    sector: str | None = None
    alert_threshold: str
    created_at: str

    model_config = {"from_attributes": True}


@router.get("")
async def list_watchlist(session: AsyncSession = Depends(get_session)):
    """List all watchlist items."""
    result = await session.execute(
        select(WatchlistItem).order_by(WatchlistItem.ticker)
    )
    items = result.scalars().all()
    return {
        "watchlist": [
            {
                "id": str(item.id),
                "ticker": item.ticker,
                "sector": item.sector,
                "alert_threshold": item.alert_threshold,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ]
    }


@router.post("", status_code=201)
async def add_to_watchlist(
    body: WatchlistCreate,
    session: AsyncSession = Depends(get_session),
):
    """Add a ticker to the watchlist."""
    ticker = body.ticker.upper()

    # Check for duplicate
    existing = await session.execute(
        select(WatchlistItem).where(WatchlistItem.ticker == ticker)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"Ticker {ticker} already in watchlist")

    valid_thresholds = {"high", "medium", "low", "none"}
    if body.alert_threshold not in valid_thresholds:
        raise HTTPException(status_code=422, detail=f"alert_threshold must be one of {valid_thresholds}")

    item = WatchlistItem(ticker=ticker, alert_threshold=body.alert_threshold)
    session.add(item)
    await session.commit()
    await session.refresh(item)

    return {
        "id": str(item.id),
        "ticker": item.ticker,
        "sector": item.sector,
        "alert_threshold": item.alert_threshold,
        "created_at": item.created_at.isoformat(),
    }


@router.delete("/{ticker}", status_code=200)
async def remove_from_watchlist(
    ticker: str,
    session: AsyncSession = Depends(get_session),
):
    """Remove a ticker from the watchlist."""
    ticker_upper = ticker.upper()
    result = await session.execute(
        select(WatchlistItem).where(WatchlistItem.ticker == ticker_upper)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker_upper} not in watchlist")

    await session.delete(item)
    await session.commit()
    return {"detail": f"Removed {ticker_upper} from watchlist"}
