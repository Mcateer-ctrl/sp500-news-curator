"""SEC 13F filings ingestion — fetches institutional investor filing data from EDGAR."""

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select

from db.database import async_session
from db.models import Sec13FFiling

logger = logging.getLogger(__name__)

MAJOR_CIKS = {
    "0001067983": "BRK.B",
    "0001166559": "GS",
    "0001364742": "BLK",
}

SEC_HEADERS = {"User-Agent": "SP500NewsCurator admin@example.com"}


async def fetch_13f_filings() -> list[Sec13FFiling]:
    filings: list[Sec13FFiling] = []
    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for cik, ticker in MAJOR_CIKS.items():
            try:
                url = f"https://data.sec.gov/submissions/CIK{cik}.json"
                resp = await client.get(url, headers=SEC_HEADERS)
                resp.raise_for_status()
                data = resp.json()

                recent = data.get("filings", {}).get("recent", {})
                forms = recent.get("form", [])
                dates = recent.get("filingDate", [])
                periods = recent.get("reportDate", [])

                for i, form in enumerate(forms):
                    if "13F" not in form:
                        continue
                    filing_date_str = dates[i] if i < len(dates) else None
                    period_str = periods[i] if i < len(periods) else None
                    if not filing_date_str or not period_str:
                        continue

                    filing_date = datetime.fromisoformat(filing_date_str).replace(tzinfo=timezone.utc)
                    if filing_date < three_months_ago:
                        continue

                    period_date = datetime.fromisoformat(period_str).replace(tzinfo=timezone.utc)
                    filings.append(Sec13FFiling(
                        ticker=ticker,
                        cik=cik,
                        filing_date=filing_date,
                        period_date=period_date,
                        shares_held=None,
                        value=None,
                    ))
            except Exception:
                logger.exception("Failed to fetch 13F for CIK %s (%s)", cik, ticker)

    logger.info("Fetched %d 13F filings", len(filings))
    return filings


async def store_13f_filings(filings: list[Sec13FFiling]) -> int:
    if not filings:
        return 0
    inserted = 0
    async with async_session() as session:
        for filing in filings:
            result = await session.execute(
                select(Sec13FFiling).where(
                    Sec13FFiling.cik == filing.cik,
                    Sec13FFiling.filing_date == filing.filing_date,
                )
            )
            if result.scalar_one_or_none():
                continue
            session.add(filing)
            inserted += 1
        if inserted:
            await session.commit()
    logger.info("Stored %d new 13F filings", inserted)
    return inserted
