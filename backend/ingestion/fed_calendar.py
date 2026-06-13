import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from db.database import async_session
from db.models import FedEvent

logger = logging.getLogger(__name__)

# FOMC meeting schedule — updated annually (2024-2025 cycle)
FOMC_SCHEDULE = [
    (datetime(2024, 1, 31, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 3, 20, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 5, 1, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 6, 12, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 7, 31, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 9, 18, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 11, 7, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2024, 12, 18, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 1, 29, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 3, 19, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 5, 7, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 6, 18, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 7, 30, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 9, 17, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 11, 6, tzinfo=timezone.utc), "FOMC Meeting"),
    (datetime(2025, 12, 10, tzinfo=timezone.utc), "FOMC Meeting"),
]


async def fetch_fed_events() -> list[FedEvent]:
    events: list[FedEvent] = []
    now = datetime.now(timezone.utc)
    for event_date, event_name in FOMC_SCHEDULE:
        if event_date < now - timedelta(days=90):
            continue
        if event_date > now + timedelta(days=180):
            continue
        events.append(FedEvent(
            event_name=event_name,
            event_date=event_date,
            event_type="rate_decision",
            actual_rate=None,
            expected_rate=None,
        ))
    return events


async def store_fed_events(events: list[FedEvent]) -> int:
    if not events:
        return 0
    inserted = 0
    async with async_session() as session:
        for event in events:
            result = await session.execute(
                select(FedEvent).where(
                    FedEvent.event_date == event.event_date,
                    FedEvent.event_name == event.event_name,
                )
            )
            if result.scalar_one_or_none():
                continue
            session.add(event)
            inserted += 1
        if inserted:
            await session.commit()
    logger.info("Stored %d new Fed events", inserted)
    return inserted
