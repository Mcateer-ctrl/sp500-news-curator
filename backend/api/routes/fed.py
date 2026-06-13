"""Federal Reserve event endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import FedEvent

router = APIRouter(prefix="/fed", tags=["fed"])


@router.get("/events")
async def list_fed_events(
    event_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    query = select(FedEvent).order_by(FedEvent.event_date)
    if event_type:
        query = query.where(FedEvent.event_type == event_type)

    result = await session.execute(query)
    rows = result.scalars().all()

    return {
        "events": [
            {
                "id": r.id,
                "event_name": r.event_name,
                "event_date": r.event_date.isoformat(),
                "event_type": r.event_type,
                "actual_rate": r.actual_rate,
                "expected_rate": r.expected_rate,
            }
            for r in rows
        ]
    }
