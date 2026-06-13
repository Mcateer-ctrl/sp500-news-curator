import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_

from config import settings
from db.database import async_session
from db.models import (
    AlertRule, Notification, ScoredArticle, WatchlistItem,
    EarningsReport, EconomicIndicator, SentimentHistory, PushSubscription,
)
from alerts.email_sender import send_email
from alerts.push_sender import send_push_notification

logger = logging.getLogger(__name__)


async def check_alerts() -> int:
    async with async_session() as session:
        result = await session.execute(
            select(AlertRule).where(AlertRule.enabled == True)
        )
        rules = list(result.scalars().all())

    if not rules:
        return 0

    now = datetime.now(timezone.utc)
    new_notifications: list[Notification] = []
    triggered_count = 0

    for rule in rules:
        triggered = await _evaluate_rule(rule, now)
        if not triggered:
            continue

        dedup_key = f"{rule.rule_type}:{rule.ticker or 'all'}:{now.date()}"
        async with async_session() as session:
            existing = await session.execute(
                select(Notification).where(
                    Notification.notification_type == rule.rule_type,
                    Notification.ticker == (rule.ticker or None),
                    Notification.created_at >= datetime.combine(now.date(), datetime.min.time(), tzinfo=timezone.utc),
                )
            )
            if existing.scalar_one_or_none():
                continue

            rule.last_triggered_at = now
            session.add(rule)

            channels = [c.strip() for c in rule.channel.split(",")]
            for channel in channels:
                notification = Notification(
                    alert_rule_id=rule.id,
                    title=_title_for(rule),
                    body=_body_for(rule),
                    ticker=rule.ticker,
                    notification_type=rule.rule_type,
                    channel=channel,
                    status="pending",
                )
                session.add(notification)
                new_notifications.append(notification)

            await session.commit()

            for n in new_notifications:
                n_id = n.id
                await _send_via_channel(n)

            triggered_count += 1
            new_notifications.clear()

    logger.info("Alert check: %d rules triggered", triggered_count)
    return triggered_count


async def _evaluate_rule(rule: AlertRule, now: datetime) -> bool:
    async with async_session() as session:
        if rule.rule_type == "sentiment_shift":
            return await _check_sentiment_shift(session, rule)
        elif rule.rule_type == "impact_threshold":
            return await _check_impact(session, rule, now)
        elif rule.rule_type == "earnings":
            return await _check_earnings(session, rule, now)
        elif rule.rule_type == "economic":
            return await _check_economic(session, rule, now)
    return False


async def _check_sentiment_shift(session, rule) -> bool:
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    cutoff_48h = now - timedelta(hours=48)

    conditions = [SentimentHistory.ticker == rule.ticker] if rule.ticker else []

    recent = await session.execute(
        select(func.avg(SentimentHistory.composite_score))
        .where(and_(
            SentimentHistory.date >= cutoff_24h,
            *conditions,
        ))
    )
    earlier = await session.execute(
        select(func.avg(SentimentHistory.composite_score))
        .where(and_(
            SentimentHistory.date >= cutoff_48h,
            SentimentHistory.date < cutoff_24h,
            *conditions,
        ))
    )
    recent_val = recent.scalar()
    earlier_val = earlier.scalar()
    if recent_val is None or earlier_val is None:
        return False
    delta = abs(recent_val - earlier_val)
    return delta >= rule.threshold


async def _check_impact(session, rule, now) -> bool:
    cutoff = now - timedelta(minutes=5)
    query = select(ScoredArticle).where(
        ScoredArticle.scored_at >= cutoff,
        ScoredArticle.impact == "high",
    )
    if rule.ticker:
        query = query.where(ScoredArticle.affected_tickers.any(rule.ticker))
    result = await session.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


async def _check_earnings(session, rule, now) -> bool:
    cutoff = now - timedelta(minutes=5)
    query = select(EarningsReport).where(
        EarningsReport.created_at >= cutoff,
    )
    if rule.ticker:
        query = query.where(EarningsReport.ticker == rule.ticker)
    result = await session.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


async def _check_economic(session, rule, now) -> bool:
    cutoff = now - timedelta(minutes=5)
    query = select(EconomicIndicator).where(
        EconomicIndicator.created_at >= cutoff,
    )
    result = await session.execute(query.limit(1))
    return result.scalar_one_or_none() is not None


def _title_for(rule: AlertRule) -> str:
    titles = {
        "sentiment_shift": f"Sentiment Shift{' for ' + rule.ticker if rule.ticker else ''}",
        "impact_threshold": f"High Impact News{' for ' + rule.ticker if rule.ticker else ''}",
        "earnings": f"Earnings Report{' for ' + rule.ticker if rule.ticker else ''}",
        "economic": "Economic Indicator Update",
    }
    return titles.get(rule.rule_type, "Alert Triggered")


def _body_for(rule: AlertRule) -> str:
    bodies = {
        "sentiment_shift": f"Sentiment has shifted by {rule.threshold} or more in the last 24 hours.",
        "impact_threshold": f"High impact article detected impacting {rule.ticker or 'watched tickers'}.",
        "earnings": f"Earnings report published for {rule.ticker or 'a watched ticker'}.",
        "economic": f"An economic indicator has been updated.",
    }
    return bodies.get(rule.rule_type, "Alert rule triggered.")


async def _send_via_channel(notification: Notification) -> None:
    async with async_session() as session:
        n = await session.get(Notification, notification.id)
        if n is None:
            return

        sent = False
        if n.channel == "email":
            sent = send_email(
                to=settings.email_to,
                subject=n.title,
                html_body=f"<h2>{n.title}</h2><p>{n.body}</p><p>Ticker: {n.ticker or 'N/A'}</p>",
            )
        elif n.channel == "push":
            result = await session.execute(
                select(PushSubscription)
            )
            subs = result.scalars().all()
            for sub in subs:
                send_push_notification(sub.endpoint, sub.p256dh_key, sub.auth_key, n.title, n.body)
            sent = True

        if sent:
            n.status = "sent"
            n.sent_at = datetime.now(timezone.utc)
        else:
            n.status = "failed"

        await session.commit()
