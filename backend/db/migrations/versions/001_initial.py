"""Initial migration — create articles, scored_articles, watchlist_items tables.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_url", sa.Text(), nullable=False, unique=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("raw_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "scored_articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "article_id",
            UUID(as_uuid=True),
            sa.ForeignKey("articles.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column("sentiment", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("impact", sa.String(20), nullable=False, server_default="low"),
        sa.Column("impact_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("time_horizon", sa.String(30), nullable=False, server_default="short_term"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("affected_tickers", ARRAY(sa.Text()), nullable=True),
        sa.Column("affected_sectors", ARRAY(sa.Text()), nullable=True),
        sa.Column("scored_by", sa.String(30), nullable=False),
        sa.Column("llm_provider", sa.String(30), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(10), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("alert_threshold", sa.String(10), nullable=False, server_default="none"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("ticker", name="uq_watchlist_ticker"),
    )


def downgrade() -> None:
    op.drop_table("watchlist_items")
    op.drop_table("scored_articles")
    op.drop_table("articles")
