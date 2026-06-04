"""
FinBERT wrapper — loads once at startup, reused across all requests.
Model weights are cached in /app/model_cache to avoid re-downloading.
"""

import asyncio
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

_pipeline = None
_lock = asyncio.Lock()


@dataclass
class FinBertResult:
    """Result from FinBERT sentiment classification."""
    positive: float
    negative: float
    neutral: float
    label: str


def _load_pipeline():
    """Load the FinBERT pipeline (synchronous, called from threadpool)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    try:
        from transformers import pipeline as hf_pipeline
        logger.info("Loading FinBERT model from %s (cache: %s)", settings.finbert_model, settings.finbert_cache_dir)
        _pipeline = hf_pipeline(
            "text-classification",
            model=settings.finbert_model,
            top_k=3,
            cache_dir=settings.finbert_cache_dir,
        )
        logger.info("FinBERT model loaded successfully.")
        return _pipeline
    except Exception:
        logger.exception("Failed to load FinBERT model")
        return None


async def get_finbert_pipeline():
    """Lazy-load FinBERT model (singleton, thread-safe)."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    async with _lock:
        if _pipeline is not None:
            return _pipeline
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _load_pipeline)


def is_loaded() -> bool:
    """Check if the FinBERT model has been loaded."""
    return _pipeline is not None


async def run_finbert(text: str) -> FinBertResult:
    """Run FinBERT inference on a text string (headline).

    Runs CPU-bound inference in a threadpool executor to avoid blocking the event loop.
    Returns neutral result with confidence=0.0 if model fails to load.
    """
    pipe = await get_finbert_pipeline()
    if pipe is None:
        logger.warning("FinBERT not available — returning neutral fallback")
        return FinBertResult(positive=0.0, negative=0.0, neutral=1.0, label="neutral")

    truncated = text[:512]

    loop = asyncio.get_running_loop()
    try:
        results = await loop.run_in_executor(None, lambda: pipe(truncated))
    except Exception:
        logger.exception("FinBERT inference failed for text: %s", text[:80])
        return FinBertResult(positive=0.0, negative=0.0, neutral=1.0, label="neutral")

    scores = {r["label"].lower(): r["score"] for r in results[0]}
    positive = scores.get("positive", 0.0)
    negative = scores.get("negative", 0.0)
    neutral = scores.get("neutral", 0.0)

    label = max(scores, key=scores.get)
    return FinBertResult(positive=positive, negative=negative, neutral=neutral, label=label)
