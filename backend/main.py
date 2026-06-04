"""FastAPI entrypoint — wires together all routes, middleware, and lifecycle events."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.middleware import setup_middleware
from api.routes import articles, health, sentiment, watchlist
from db.database import engine
from db.models import Base
from db.seed import seed
from ingestion.scheduler import start_scheduler, stop_scheduler, ingest_all_sources

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # Create tables if they don't exist (in dev; use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

    # Seed watchlist
    try:
        await seed()
    except Exception:
        logger.exception("Seed failed (may already be seeded)")

    # Pre-warm FinBERT in background
    try:
        from analysis.finbert import get_finbert_pipeline
        await get_finbert_pipeline()
    except Exception:
        logger.exception("FinBERT pre-warm failed — will try again on first use")

    # Start scheduler
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="S&P 500 News Sentiment Curator",
    description="Ingest, analyze, and serve financial news with AI-powered sentiment scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

setup_middleware(app)

# Register routes
app.include_router(health.router)
app.include_router(articles.router)
app.include_router(sentiment.router)
app.include_router(watchlist.router)


@app.post("/ingest/trigger", tags=["ingestion"])
async def trigger_ingestion():
    """Manually trigger ingestion from all sources (for dev/testing)."""
    result = await ingest_all_sources()
    return {"status": "ok", **result}
