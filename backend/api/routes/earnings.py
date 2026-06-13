"""Earnings report endpoints."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import EarningsReport

router = APIRouter(prefix="/earnings", tags=["earnings"])


@router.get("")
async def list_earnings(
    ticker: Optional[str] = Query(None),
    upcoming: bool = Query(False),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    """List earnings reports with optional filters."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days) if not upcoming else now
    end = now + timedelta(days=days) if upcoming else now

    query = select(EarningsReport).where(
        and_(EarningsReport.report_date >= cutoff, EarningsReport.report_date <= end)
    ).order_by(EarningsReport.report_date)

    if ticker:
        query = query.where(EarningsReport.ticker == ticker.upper())

    result = await session.execute(query)
    rows = result.scalars().all()

    return {
        "earnings": [
            {
                "id": r.id,
                "ticker": r.ticker,
                "fiscal_quarter": r.fiscal_quarter,
                "eps_estimate": r.eps_estimate,
                "eps_actual": r.eps_actual,
                "revenue_estimate": r.revenue_estimate,
                "revenue_actual": r.revenue_actual,
                "report_date": r.report_date.isoformat(),
                "report_time": r.report_time,
            }
            for r in rows
        ]
    }
