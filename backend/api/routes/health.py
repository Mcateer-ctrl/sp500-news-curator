"""Health check endpoints."""

from fastapi import APIRouter

from analysis.finbert import is_loaded as finbert_is_loaded
from analysis.llm_client import test_llm_connection
from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Basic health check."""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "finbert_loaded": finbert_is_loaded(),
    }


@router.get("/health/llm")
async def health_llm():
    """Test the configured LLM provider with a simple prompt."""
    result = await test_llm_connection()
    return result
