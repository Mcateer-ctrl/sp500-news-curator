"""Unified LLM client supporting four interchangeable backends.

Routes to the correct provider based on settings.llm_provider.
All providers share the same prompt template and return the same result type.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a financial analyst AI. Analyze news articles for their potential \
impact on S&P 500 stock prices. Always respond with valid JSON only — no prose, \
no markdown, no explanation outside the JSON object."""

USER_PROMPT_TEMPLATE = """Analyze this article and respond with exactly this JSON structure:
{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "confidence": <float 0.0-1.0>,
  "impact": "high" | "medium" | "low",
  "impact_reason": "<one sentence>",
  "affected_tickers": ["TICKER", ...],
  "affected_sectors": ["Sector", ...],
  "time_horizon": "immediate" | "short_term" | "long_term",
  "summary": "<2 sentence plain English summary for investors>"
}}

Rules:
- impact=high means this could move a stock >2% at open
- Only list tickers directly and materially affected
- confidence reflects how clearly bullish or bearish the signal is
- If genuinely market-neutral, sentiment=neutral with confidence>0.8

Headline: {headline}

Body: {body}"""


@dataclass
class LLMSentimentResult:
    """Parsed LLM sentiment analysis result."""
    sentiment: str
    confidence: float
    impact: str
    impact_reason: str
    affected_tickers: list[str] = field(default_factory=list)
    affected_sectors: list[str] = field(default_factory=list)
    time_horizon: str = "short_term"
    summary: str = ""


def _parse_llm_response(text: str) -> Optional[LLMSentimentResult]:
    """Parse JSON from LLM response text, stripping markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return None

    valid_sentiments = {"bullish", "bearish", "neutral"}
    valid_impacts = {"high", "medium", "low"}
    valid_horizons = {"immediate", "short_term", "long_term"}

    sentiment = data.get("sentiment", "neutral")
    if sentiment not in valid_sentiments:
        sentiment = "neutral"

    impact = data.get("impact", "low")
    if impact not in valid_impacts:
        impact = "low"

    horizon = data.get("time_horizon", "short_term")
    if horizon not in valid_horizons:
        horizon = "short_term"

    return LLMSentimentResult(
        sentiment=sentiment,
        confidence=float(data.get("confidence", 0.5)),
        impact=impact,
        impact_reason=str(data.get("impact_reason", "")),
        affected_tickers=data.get("affected_tickers", []),
        affected_sectors=data.get("affected_sectors", []),
        time_horizon=horizon,
        summary=str(data.get("summary", "")),
    )


async def _call_lmstudio(headline: str, body: str) -> Optional[str]:
    """Call LM Studio's OpenAI-compatible API."""
    user_msg = USER_PROMPT_TEMPLATE.format(headline=headline, body=body)
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.1,
    }
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(f"{settings.lmstudio_base_url}/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_gemini(headline: str, body: str) -> Optional[str]:
    """Call Google Gemini via the generativeai SDK."""
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    # Use settings.llm_model if provided, fallback to gemini-2.0-flash (free, widely available)
    model_name = settings.llm_model or "gemini-2.0-flash"
    model = genai.GenerativeModel(model_name)
    user_msg = USER_PROMPT_TEMPLATE.format(headline=headline, body=body)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{user_msg}"

    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, lambda: model.generate_content(full_prompt))
    return response.text


async def _call_openrouter(headline: str, body: str) -> Optional[str]:
    """Call OpenRouter (OpenAI-compatible API)."""
    user_msg = USER_PROMPT_TEMPLATE.format(headline=headline, body=body)
    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "SP500NewsCurator",
    }
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _call_anthropic(headline: str, body: str) -> Optional[str]:
    """Call Anthropic Claude via the anthropic SDK."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    user_msg = USER_PROMPT_TEMPLATE.format(headline=headline, body=body)
    message = await client.messages.create(
        model=settings.llm_model or "claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return message.content[0].text


_PROVIDERS = {
    "lmstudio": _call_lmstudio,
    "gemini": _call_gemini,
    "openrouter": _call_openrouter,
    "anthropic": _call_anthropic,
}


async def score_with_llm(headline: str, body: str) -> Optional[LLMSentimentResult]:
    """Score an article using the configured LLM provider.

    Attempts to parse JSON from the LLM response. Retries once on malformed JSON.
    Returns None if both attempts fail.
    """
    provider_fn = _PROVIDERS.get(settings.llm_provider)
    if provider_fn is None:
        logger.error("Unknown LLM provider: %s", settings.llm_provider)
        return None

    for attempt in range(2):
        try:
            if attempt == 0:
                raw = await asyncio.wait_for(
                    provider_fn(headline, body),
                    timeout=settings.llm_timeout_seconds,
                )
            else:
                logger.info("Retrying LLM call with JSON reminder (attempt 2)")
                retry_body = body + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation."
                raw = await asyncio.wait_for(
                    provider_fn(headline, retry_body),
                    timeout=settings.llm_timeout_seconds,
                )

            if raw is None:
                logger.warning("LLM returned None (provider=%s)", settings.llm_provider)
                return None

            result = _parse_llm_response(raw)
            if result is not None:
                return result

            logger.warning("LLM returned malformed JSON (attempt %d): %s", attempt + 1, raw[:200])

        except asyncio.TimeoutError:
            logger.warning("LLM call timed out (provider=%s, attempt=%d)", settings.llm_provider, attempt + 1)
            return None
        except Exception:
            logger.exception("LLM call failed (provider=%s, attempt=%d)", settings.llm_provider, attempt + 1)
            if attempt == 1:
                return None

    return None


async def test_llm_connection() -> dict:
    """Test the configured LLM provider with a simple prompt. Returns status dict."""
    import time

    provider_fn = _PROVIDERS.get(settings.llm_provider)
    if provider_fn is None:
        return {"ok": False, "error": f"Unknown provider: {settings.llm_provider}", "latency_ms": 0,
                "provider": settings.llm_provider, "model": settings.llm_model}

    start = time.monotonic()
    try:
        raw = await asyncio.wait_for(
            provider_fn("Test headline", "Test body"),
            timeout=settings.llm_timeout_seconds,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        return {"ok": True, "latency_ms": latency_ms, "provider": settings.llm_provider,
                "model": settings.llm_model, "error": None}
    except Exception as e:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {"ok": False, "latency_ms": latency_ms, "provider": settings.llm_provider,
                "model": settings.llm_model, "error": str(e)}
