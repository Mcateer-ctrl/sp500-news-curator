import logging
from datetime import datetime, timezone

from fredapi import Fred
from sqlalchemy import select

from config import settings
from db.database import async_session
from db.models import EconomicIndicator

logger = logging.getLogger(__name__)

DEFAULT_INDICATORS = {
    "cpi": "CPIAUCSL",
    "nonfarm_payrolls": "PAYEMS",
    "fed_funds_rate": "FEDFUNDS",
    "unemployment_rate": "UNRATE",
    "gdp": "GDP",
}

fred: Fred | None = None

def _get_fred() -> Fred:
    global fred
    if fred is None:
        fred = Fred(api_key=settings.fred_api_key)
    return fred

async def fetch_indicator(indicator_name: str, series_id: str, observation_count: int = 3) -> list[EconomicIndicator]:
    try:
        data = _get_fred().get_series_latest_release(series_id)
        if data is None or data.empty:
            return []
        results = []
        values = data.tail(observation_count)
        for idx, (date_val, value) in enumerate(values.items()):
            prev = float(values.iloc[idx - 1]) if idx > 0 else None
            if hasattr(date_val, 'to_pydatetime'):
                dt = date_val.to_pydatetime().replace(tzinfo=timezone.utc)
            else:
                dt = datetime.combine(date_val, datetime.min.time(), tzinfo=timezone.utc)
            results.append(EconomicIndicator(
                indicator_name=indicator_name,
                value=float(value),
                previous_value=prev,
                date=dt,
                source="fred",
            ))
        return results
    except Exception:
        logger.exception("Failed to fetch indicator %s (%s)", indicator_name, series_id)
        return []

async def fetch_all_indicators() -> list[EconomicIndicator]:
    all_indicators: list[EconomicIndicator] = []
    for name, series_id in DEFAULT_INDICATORS.items():
        indicators = await fetch_indicator(name, series_id)
        all_indicators.extend(indicators)
    return all_indicators

async def store_indicators(indicators: list[EconomicIndicator]) -> int:
    if not indicators:
        return 0
    inserted = 0
    async with async_session() as session:
        for indicator in indicators:
            result = await session.execute(
                select(EconomicIndicator).where(
                    EconomicIndicator.indicator_name == indicator.indicator_name,
                    EconomicIndicator.date == indicator.date,
                )
            )
            if result.scalar_one_or_none():
                continue
            session.add(indicator)
            inserted += 1
        if inserted:
            await session.commit()
    logger.info("Stored %d new economic indicators", inserted)
    return inserted
