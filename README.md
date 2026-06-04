# S&P 500 News Sentiment Curator

A full-stack web application that ingests financial news from multiple sources, scores sentiment using **FinBERT** (local, free) as a pre-filter and a **configurable LLM** for deep analysis, maps articles to S&P 500 tickers and sectors, and serves everything via a React dashboard.

---

## What It Does

**In 30 seconds:**

1. **Ingests** news from NewsAPI, Reuters/AP RSS feeds, and SEC EDGAR
2. **Scores** each article using FinBERT (headline) → LLM (deep analysis)
3. **Maps** articles to S&P 500 tickers and sectors automatically
4. **Categorizes** sentiment (bullish/bearish/neutral) with confidence scores and impact levels
5. **Displays** results in a real-time React dashboard with filtering, charts, and watchlist

**Key Features:**
- ✅ Two-stage sentiment pipeline (fast local FinBERT + deep LLM analysis)
- ✅ Support 4 LLM providers (LM Studio, Gemini, OpenRouter, Anthropic) — swap providers via `.env`
- ✅ Automatic ticker/sector mapping from article text
- ✅ Respects rate limits (configurable concurrent calls)
- ✅ Fully containerized with Docker — no local dependencies except Docker Desktop
- ✅ REST API + interactive React dashboard

---

## Prerequisites

- **Docker Desktop** (with Docker Compose v2)
- (Optional) **LM Studio** — for free local LLM inference
- (Optional) API keys for Gemini, OpenRouter, or Anthropic

---

## Quick Start

```bash
# 1. Clone the repo
cd sp500-news-curator

# 2. Copy and configure environment
cp .env.example .env

# 3. Edit .env — at minimum, choose an LLM provider (see below)
#    LM Studio works out of the box if running on your host machine

# 4. Start all services
docker-compose up --build

# 5. Open the dashboard
open http://localhost
```

The backend API is available at `http://localhost:8000` and the frontend dev server at `http://localhost:5173`. Nginx proxies both at port 80.

---

## LLM Provider Setup

The application supports four interchangeable LLM backends. Change provider by setting `LLM_PROVIDER` in `.env` — no code changes needed.

### LM Studio (Local — Free)

1. Download [LM Studio](https://lmstudio.ai/)
2. Load a model (e.g., Mistral 7B Instruct)
3. Start the local server (it runs on port 1234 by default)
4. Set in `.env`:
   ```
   LLM_PROVIDER=lmstudio
   LLM_MODEL=mistral
   LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1
   ```

### Google Gemini (Free Tier Available)

1. Get an API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set in `.env`:
   ```
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-key-here
   LLM_MODEL=gemini-2.0-flash
   ```

### OpenRouter (100+ Models)

1. Get an API key at [OpenRouter](https://openrouter.ai/keys)
2. Set in `.env`:
   ```
   LLM_PROVIDER=openrouter
   OPENROUTER_API_KEY=your-key-here
   LLM_MODEL=mistralai/mistral-7b-instruct:free
   ```
   Other free models: `meta-llama/llama-3-8b-instruct:free`, `google/gemma-7b-it:free`

### Anthropic Claude

1. Get an API key at [Anthropic Console](https://console.anthropic.com/)
2. Set in `.env`:
   ```
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your-key-here
   LLM_MODEL=claude-haiku-4-5-20251001
   ```

---

## Configuration & Rate Limits

All pipeline behavior is configurable via `.env`:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `lmstudio` | LLM backend: `lmstudio`, `gemini`, `openrouter`, or `anthropic` |
| `LLM_MODEL` | `mistral` | Model name for the chosen provider (e.g., `gemini-1.5-flash`) |
| `INGEST_INTERVAL_MINUTES` | `30` | How often to fetch new articles |
| `MAX_CONCURRENT_LLM_CALLS` | `1` | Maximum simultaneous LLM requests (rate limit safety) |
| `LLM_TIMEOUT_SECONDS` | `30` | Timeout per LLM call |
| `FINBERT_NEUTRAL_THRESHOLD` | `0.85` | If FinBERT neutral score above this, skip LLM call |
| `MAX_ARTICLE_BODY_CHARS` | `3000` | Truncate article body before sending to LLM |

### Rate Limit Guidance

**Gemini** (free tier): ~15–30 RPM (requests per minute). `gemini-2.0-flash` is fast, free, and widely available.
- Set `MAX_CONCURRENT_LLM_CALLS=1` to stay well within limits
- Ingestion every 30 minutes naturally spreads load

**Other Providers**: Check their documentation
- `openrouter`: Free models often have per-minute limits
- `anthropic`: Claude Haiku is rate-limited; check your account dashboard
- `lmstudio`: No external limits (local inference)

---

## Architecture Overview

| Service | Description |
|---|---|
| **postgres** | PostgreSQL 16 database for articles, scores, and watchlist |
| **redis** | Redis 7 for caching (future use) |
| **backend** | FastAPI Python app — ingestion, FinBERT, LLM scoring, REST API |
| **frontend** | React 18 + Vite + TypeScript + Tailwind dashboard |
| **nginx** | Reverse proxy — `/api/` → backend, `/` → frontend |

### Sentiment Pipeline

1. **FinBERT** runs on every headline (fast, free, local)
2. If FinBERT isn't confidently neutral (< 85% neutral), the article is sent to the configured **LLM** for deep analysis
3. The LLM returns structured JSON with sentiment, impact, affected tickers, and a summary
4. If the LLM fails, the pipeline falls back to FinBERT-only scoring

---

## API Reference

### Health
```bash
# Basic health check
curl http://localhost:8000/health

# Test LLM connection
curl http://localhost:8000/health/llm
```

### Articles
```bash
# List articles (last 24h, paginated)
curl "http://localhost:8000/articles?hours=24&limit=50"

# Filter by ticker
curl "http://localhost:8000/articles?ticker=AAPL"

# Filter by sentiment
curl "http://localhost:8000/articles?sentiment=bullish"

# Filter by impact
curl "http://localhost:8000/articles?impact=high"

# Get single article
curl http://localhost:8000/articles/{article-uuid}
```

### Sentiment
```bash
# Ticker sentiment trend (7 days)
curl http://localhost:8000/sentiment/ticker/AAPL

# Sector sentiment summary (24h)
curl http://localhost:8000/sentiment/sectors
```

### Watchlist
```bash
# List watchlist
curl http://localhost:8000/watchlist

# Add ticker
curl -X POST http://localhost:8000/watchlist \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "alert_threshold": "high"}'

# Remove ticker
curl -X DELETE http://localhost:8000/watchlist/AAPL
```

### Ingestion
```bash
# Manually trigger ingestion
curl -X POST http://localhost:8000/ingest/trigger
```

---

## Development Tips

### View Logs
```bash
# All services
docker-compose logs -f

# Single service
docker-compose logs -f backend
```

### Trigger Manual Ingestion
```bash
curl -X POST http://localhost:8000/ingest/trigger
```

### Access the Database
```bash
docker-compose exec postgres psql -U newsuser -d sp500news
```

### Rebuild a Single Service
```bash
docker-compose up --build backend
```

### FinBERT Model Cache
FinBERT weights are baked into the backend Docker image at build time and also mounted as a volume (`model_cache`). The model is **not** re-downloaded on subsequent startups.
