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
