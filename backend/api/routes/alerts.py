from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import AlertRule, Notification, PushSubscription

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertRuleCreate(BaseModel):
    ticker: Optional[str] = None
    rule_type: str
    threshold: float
    channel: str = "in_app"


class AlertRuleUpdate(BaseModel):
    ticker: Optional[str] = None
    threshold: Optional[float] = None
    channel: Optional[str] = None
    enabled: Optional[bool] = None


class PushSubscribeBody(BaseModel):
    endpoint: str
    p256dh_key: str
    auth_key: str


@router.get("/rules")
async def list_rules(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(AlertRule).order_by(AlertRule.created_at.desc())
    )
    rules = result.scalars().all()
    return {
        "rules": [
            {
                "id": r.id,
                "ticker": r.ticker,
                "rule_type": r.rule_type,
                "threshold": r.threshold,
                "channel": r.channel,
                "enabled": r.enabled,
                "last_triggered_at": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in rules
        ]
    }


@router.post("/rules", status_code=201)
async def create_rule(body: AlertRuleCreate, session: AsyncSession = Depends(get_session)):
    valid_types = {"sentiment_shift", "impact_threshold", "earnings", "economic"}
    if body.rule_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"rule_type must be one of {valid_types}")

    rule = AlertRule(
        ticker=body.ticker.upper() if body.ticker else None,
        rule_type=body.rule_type,
        threshold=body.threshold,
        channel=body.channel,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return {
        "id": rule.id,
        "ticker": rule.ticker,
        "rule_type": rule.rule_type,
        "threshold": rule.threshold,
        "channel": rule.channel,
        "enabled": rule.enabled,
        "created_at": rule.created_at.isoformat(),
    }


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: int, body: AlertRuleUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    if body.ticker is not None:
        rule.ticker = body.ticker.upper() if body.ticker else None
    if body.threshold is not None:
        rule.threshold = body.threshold
    if body.channel is not None:
        rule.channel = body.channel
    if body.enabled is not None:
        rule.enabled = body.enabled

    await session.commit()
    await session.refresh(rule)
    return {"id": rule.id, "ticker": rule.ticker, "rule_type": rule.rule_type, "threshold": rule.threshold, "channel": rule.channel, "enabled": rule.enabled}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    await session.delete(rule)
    await session.commit()
    return {"detail": "Rule deleted"}


@router.get("/notifications")
async def list_notifications(
    unread: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    query = select(Notification).order_by(Notification.created_at.desc()).limit(limit)
    if unread:
        query = query.where(Notification.read_at.is_(None))
    result = await session.execute(query)
    notifications = result.scalars().all()
    return {
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "ticker": n.ticker,
                "notification_type": n.notification_type,
                "channel": n.channel,
                "status": n.status,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }


@router.put("/notifications/{notification_id}/read")
async def mark_read(notification_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Notification).where(Notification.id == notification_id))
    n = result.scalar_one_or_none()
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read_at = datetime.now(timezone.utc)
    await session.commit()
    return {"detail": "Marked read"}


@router.post("/notifications/read-all")
async def mark_all_read(session: AsyncSession = Depends(get_session)):
    await session.execute(
        update(Notification).where(Notification.read_at.is_(None)).values(read_at=datetime.now(timezone.utc))
    )
    await session.commit()
    return {"detail": "All marked read"}


@router.post("/push/subscribe")
async def push_subscribe(body: PushSubscribeBody, session: AsyncSession = Depends(get_session)):
    existing = await session.execute(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )
    if existing.scalar_one_or_none():
        return {"detail": "Already subscribed"}

    sub = PushSubscription(
        endpoint=body.endpoint,
        p256dh_key=body.p256dh_key,
        auth_key=body.auth_key,
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    return {"id": sub.id, "detail": "Subscribed"}


@router.delete("/push/subscribe")
async def push_unsubscribe(body: PushSubscribeBody, session: AsyncSession = Depends(get_session)):
    await session.execute(
        delete(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )
    await session.commit()
    return {"detail": "Unsubscribed"}
