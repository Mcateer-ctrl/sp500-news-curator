"""SQLAlchemy ORM models for the S&P 500 News Sentiment Curator."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Article(Base):
    """Raw ingested news article."""

    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    raw_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    scored_article: Mapped["ScoredArticle | None"] = relationship(
        back_populates="article", uselist=False, lazy="selectin"
    )


class ScoredArticle(Base):
    """Sentiment scoring result for an article."""

    __tablename__ = "scored_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    impact: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    impact_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    time_horizon: Mapped[str] = mapped_column(String(30), nullable=False, default="short_term")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    affected_tickers: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    affected_sectors: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    scored_by: Mapped[str] = mapped_column(String(30), nullable=False)
    llm_provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    article: Mapped["Article"] = relationship(back_populates="scored_article", lazy="selectin")


class WatchlistItem(Base):
    """User watchlist entry for a ticker."""

    __tablename__ = "watchlist_items"
    __table_args__ = (UniqueConstraint("ticker", name="uq_watchlist_ticker"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alert_threshold: Mapped[str] = mapped_column(String(10), nullable=False, default="none")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SentimentHistory(Base):
    """Aggregated daily sentiment data for a ticker."""

    __tablename__ = "sentiment_history"
    __table_args__ = (UniqueConstraint("ticker", "date", name="uq_ticker_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    bullish_count: Mapped[int] = mapped_column(default=0)
    bearish_count: Mapped[int] = mapped_column(default=0)
    neutral_count: Mapped[int] = mapped_column(default=0)
    total_articles: Mapped[int] = mapped_column(default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    composite_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class EarningsReport(Base):
    """Corporate earnings report data."""

    __tablename__ = "earnings_reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    fiscal_quarter: Mapped[str | None] = mapped_column(String(20), nullable=True)
    eps_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps_actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    report_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class EconomicIndicator(Base):
    """Macroeconomic indicator data point."""

    __tablename__ = "economic_indicators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    indicator_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="fred")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

class Sec13FFiling(Base):
    """SEC 13F institutional filing data."""

    __tablename__ = "sec_13f_filings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    cik: Mapped[str | None] = mapped_column(String(20), nullable=True)
    filing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    shares_held: Mapped[float | None] = mapped_column(Float, nullable=True)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FedEvent(Base):
    """Federal Reserve event data."""

    __tablename__ = "fed_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    actual_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str | None] = mapped_column(String(10), nullable=True)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="in_app")
    enabled: Mapped[bool] = mapped_column(default=True)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_rule_id: Mapped[int | None] = mapped_column(
        ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ticker: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notification_type: Mapped[str] = mapped_column(String(20), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh_key: Mapped[str] = mapped_column(Text, nullable=False)
    auth_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
