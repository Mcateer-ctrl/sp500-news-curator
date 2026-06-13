"""SEC 13F institutional filing endpoints."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Sec13FFiling

router = APIRouter(prefix="/13f", tags=["13f"])


@router.get("/filings")
async def list_13f_filings(
    ticker: Optional[str] = Query(None),
    days: int = Query(90, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(Sec13FFiling).where(Sec13FFiling.filing_date >= cutoff).order_by(Sec13FFiling.filing_date.desc())

    if ticker:
        query = query.where(Sec13FFiling.ticker == ticker.upper())

    result = await session.execute(query.limit(50))
    rows = result.scalars().all()

    return {
        "filings": [
            {
                "id": r.id,
                "ticker": r.ticker,
                "cik": r.cik,
                "filing_date": r.filing_date.isoformat(),
                "period_date": r.period_date.isoformat(),
                "shares_held": r.shares_held,
                "value": r.value,
            }
            for r in rows
        ]
    }
