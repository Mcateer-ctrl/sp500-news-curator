from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import EconomicIndicator

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("")
async def list_indicators(
    names: str = Query("cpi,nonfarm_payrolls,unemployment_rate"),
    days: int = Query(90, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    indicator_names = [n.strip() for n in names.split(",")]
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = {}
    for name in indicator_names:
        query = (
            select(EconomicIndicator)
            .where(
                and_(
                    EconomicIndicator.indicator_name == name,
                    EconomicIndicator.date >= cutoff,
                )
            )
            .order_by(EconomicIndicator.date.desc())
        )
        rows = (await session.execute(query)).scalars().all()
        result[name] = [
            {
                "date": r.date.isoformat(),
                "value": r.value,
                "previous_value": r.previous_value,
                "source": r.source,
            }
            for r in rows
        ]

    return {"indicators": result}
