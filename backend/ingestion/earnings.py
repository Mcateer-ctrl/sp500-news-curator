import logging
from datetime import datetime, timezone, timedelta

import yfinance as yf
from sqlalchemy import select

from db.database import async_session
from db.models import EarningsReport

logger = logging.getLogger(__name__)


async def fetch_earnings(tickers: list[str]) -> list[EarningsReport]:
    earnings_list: list[EarningsReport] = []
    for ticker in tickers:
        try:
            tk = yf.Ticker(ticker)
            cal = tk.calendar
            if not cal:
                continue
            earnings_date = cal.get("Earnings Date")
            if not earnings_date:
                continue
            if isinstance(earnings_date, list):
                earnings_date = earnings_date[0]

            report = EarningsReport(
                ticker=ticker,
                fiscal_quarter=cal.get("Earnings Quarter Start"),
                eps_estimate=cal.get("EPS Estimate"),
                eps_actual=cal.get("EPS Actual"),
                revenue_estimate=cal.get("Revenue Estimate"),
                revenue_actual=cal.get("Revenue Actual"),
                report_date=earnings_date,
                report_time="bmo" if earnings_date.hour < 12 else "amc",
            )
            earnings_list.append(report)
        except Exception:
            logger.exception("Failed to fetch earnings for %s", ticker)
    return earnings_list


async def store_earnings(reports: list[EarningsReport]) -> int:
    if not reports:
        return 0
    inserted = 0
    async with async_session() as session:
        for report in reports:
            result = await session.execute(
                select(EarningsReport).where(
                    EarningsReport.ticker == report.ticker,
                    EarningsReport.report_date == report.report_date,
                )
            )
            if result.scalar_one_or_none():
                continue
            session.add(report)
            inserted += 1
        if inserted:
            await session.commit()
    logger.info("Stored %d new earnings reports", inserted)
    return inserted


async def update_earnings_actuals(session) -> int:
    """For recently reported earnings, fetch actual results and compute surprise."""
    result = await session.execute(
        select(EarningsReport).where(
            EarningsReport.report_date <= datetime.now(timezone.utc),
            EarningsReport.report_date >= datetime.now(timezone.utc) - timedelta(days=30),
            EarningsReport.eps_actual.is_(None),
        )
    )
    recent = list(result.scalars().all())

    updated = 0
    for report in recent:
        try:
            tk = yf.Ticker(report.ticker)
            cal = tk.calendar
            if not cal:
                continue
            eps_actual = cal.get("EPS Actual")
            revenue_actual = cal.get("Revenue Actual")
            if eps_actual is not None:
                report.eps_actual = float(eps_actual)
                if report.eps_estimate:
                    report.surprise_percent = round(
                        (report.eps_actual - report.eps_estimate) / abs(report.eps_estimate) * 100, 2
                    )
                updated += 1
            if revenue_actual is not None:
                report.revenue_actual = float(revenue_actual)
        except Exception:
            logger.exception("Failed to update actuals for %s", report.ticker)

    if updated:
        await session.commit()
    logger.info("Updated actuals for %d earnings reports", updated)
    return updated
