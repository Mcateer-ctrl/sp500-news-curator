# Agent Build Prompt: S&P 500 News Sentiment Curator

## Mission

You are an expert full-stack engineer. Your task is to build a complete, production-ready **S&P 500 News Sentiment Curator** application from scratch. Follow every instruction precisely. Build the entire project in one continuous session — do not stop and ask for clarification unless a critical ambiguity would cause data loss or security risk.

---

## Project Overview

A full-stack web application that:
- Ingests news from multiple sources (news APIs, SEC/EDGAR, RSS feeds)
- Scores sentiment using **FinBERT** (local, free) as a pre-filter and a **configurable LLM** for deep analysis
- Maps articles to S&P 500 tickers and sectors
- Exposes a REST API serving a React dashboard
- Runs entirely in **Docker** via `docker-compose`

---

## LLM Provider System (Critical Requirement)

The application must support **four interchangeable LLM backends** via a single environment variable `LLM_PROVIDER`. All providers must share a unified interface — swapping providers requires only changing `.env`, never code.

| Provider | `LLM_PROVIDER` value | Auth | Notes |
|---|---|---|---|
| LM Studio (local) | `lmstudio` | None | Uses OpenAI-compatible API at configurable host |
| Google Gemini | `gemini` | `GEMINI_API_KEY` | Free tier available |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | Access to 100+ models |
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` | High quality, paid |

The model name must also be configurable per provider via `LLM_MODEL` in `.env`.

---

## Directory Structure

Build exactly this structure:

```
sp500-news-curator/
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # FastAPI entrypoint
│   ├── config.py                # All settings via pydantic-settings
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── scheduler.py         # APScheduler jobs
│   │   ├── news_api.py          # NewsAPI.org client
│   │   ├── rss_feeds.py         # Reuters/AP RSS scraper
│   │   └── sec_edgar.py         # SEC EDGAR RSS client
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── finbert.py           # FinBERT wrapper (singleton, lazy load)
│   │   ├── llm_client.py        # Unified LLM interface (all 4 providers)
│   │   ├── sentiment_pipeline.py # Orchestrates FinBERT → LLM pipeline
│   │   └── ticker_mapper.py     # Maps text → S&P 500 tickers/sectors
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── articles.py      # GET /articles, GET /articles/{id}
│   │   │   ├── sentiment.py     # GET /sentiment/ticker/{ticker}
│   │   │   ├── watchlist.py     # CRUD /watchlist
│   │   │   └── health.py        # GET /health, GET /health/llm
│   │   └── middleware.py        # CORS, rate limiting
│   │
│   └── db/
│       ├── __init__.py
│       ├── models.py            # SQLAlchemy models
│       ├── database.py          # Async engine + session factory
│       └── migrations/          # Alembic migrations
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       │   └── client.ts        # Axios client
│       ├── components/
│       │   ├── NewsFeed.tsx
│       │   ├── SentimentChart.tsx
│       │   ├── TickerFilter.tsx
│       │   ├── ImpactBadge.tsx
│       │   └── Watchlist.tsx
│       └── pages/
│           ├── Dashboard.tsx
│           └── Settings.tsx
│
└── nginx/
    └── nginx.conf               # Reverse proxy: /api → backend, / → frontend
```

---

## Step 1 — Repository & Environment Setup

1. Create the directory structure above.
2. Initialise a git repository.
3. Create `.gitignore` — exclude: `.env`, `__pycache__`, `node_modules`, `*.pyc`, `model_cache/`, `postgres_data/`.
4. Create `.env.example` with every variable listed in the Configuration section below. Never create a real `.env` — only `.env.example`.

---

## Step 2 — Docker Compose

Create `docker-compose.yml` with these services:

**postgres**
- Image: `postgres:16-alpine`
- Environment: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` from env
- Volume: `postgres_data:/var/lib/postgresql/data`
- Healthcheck: `pg_isready`

**redis**
- Image: `redis:7-alpine`
- Volume: `redis_data:/data`
- Healthcheck: `redis-cli ping`

**backend**
- Build: `./backend`
- Depends on: postgres (healthy), redis (healthy)
- Volumes: `./backend:/app`, `model_cache:/app/model_cache` (for FinBERT weights)
- Env file: `.env`
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- Ports: `8000:8000` (dev only — in prod, only nginx exposes ports)

**frontend**
- Build: `./frontend`
- Depends on: backend
- Volumes: `./frontend:/app`, `/app/node_modules`
- Command: `npm run dev -- --host`
- Ports: `5173:5173` (dev only)

**nginx**
- Image: `nginx:alpine`
- Depends on: frontend, backend
- Ports: `80:80`
- Volumes: `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro`

**Volumes declared:** `postgres_data`, `redis_data`, `model_cache`

---

## Step 3 — Configuration (`backend/config.py`)

Use `pydantic-settings` to load all config from environment. Every setting must have a sensible default except secrets.

```python
class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:pass@postgres:5432/sp500news"
    redis_url: str = "redis://redis:6379"

    # LLM Provider — one of: lmstudio | gemini | openrouter | anthropic
    llm_provider: str = "lmstudio"
    llm_model: str = "mistral"           # model name/id for the chosen provider

    # LM Studio
    lmstudio_base_url: str = "http://host.docker.internal:1234/v1"

    # External API keys (all optional — only needed for their respective provider)
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    anthropic_api_key: str = ""

    # News data sources
    newsapi_key: str = ""                # newsapi.org free key

    # FinBERT
    finbert_model: str = "ProsusAI/finbert"
    finbert_cache_dir: str = "/app/model_cache"
    finbert_neutral_threshold: float = 0.85   # skip LLM if FinBERT neutral > this

    # Pipeline
    ingest_interval_minutes: int = 30
    max_article_body_chars: int = 3000
    llm_timeout_seconds: int = 30

    model_config = SettingsConfig(env_file=".env", case_sensitive=False)
```

---

## Step 4 — Database Models (`backend/db/models.py`)

Use SQLAlchemy 2.0 async ORM with these models:

**Article**
```
id (UUID, PK), headline (Text), body (Text), source_url (Text, unique),
published_at (DateTime), source_name (Varchar), raw_json (JSONB),
created_at (DateTime, default now)
```

**ScoredArticle**
```
id (UUID, PK), article_id (UUID, FK → Article),
sentiment (Varchar: bullish/bearish/neutral),
confidence (Float), impact (Varchar: high/medium/low),
impact_reason (Text), time_horizon (Varchar),
summary (Text), affected_tickers (ARRAY Text),
affected_sectors (ARRAY Text), scored_by (Varchar: finbert/llm),
llm_provider (Varchar, nullable), scored_at (DateTime, default now)
```

**WatchlistItem**
```
id (UUID, PK), ticker (Varchar), sector (Varchar, nullable),
alert_threshold (Varchar: high/medium/low/none),
created_at (DateTime, default now)
UNIQUE constraint on ticker
```

Set up Alembic for migrations. Create the initial migration. Add a seed script that populates WatchlistItem with 10 well-known S&P 500 tickers (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, JPM, JNJ, UNH).

---

## Step 5 — FinBERT Wrapper (`backend/analysis/finbert.py`)

```python
"""
FinBERT wrapper — loads once at startup, reused across all requests.
Model weights are cached in /app/model_cache to avoid re-downloading.
"""
```

Requirements:
- Singleton pattern — load model once on first use (lazy init), never reload
- Use `ProsusAI/finbert` via HuggingFace `transformers` pipeline
- Cache weights to `settings.finbert_cache_dir`
- Input: headline string (body is too long for BERT's 512 token limit — truncate to first 512 tokens if needed)
- Output: `FinBertResult(positive: float, negative: float, neutral: float, label: str)`
- If model fails to load, log warning and return neutral result with `confidence=0.0` — never crash the pipeline
- Run inference in a threadpool executor (it's CPU-bound, don't block the event loop)

---

## Step 6 — Unified LLM Client (`backend/analysis/llm_client.py`)

This is the most important module. It must implement a single async function:

```python
async def score_with_llm(headline: str, body: str) -> LLMSentimentResult | None:
    ...
```

that routes to the correct provider based on `settings.llm_provider`.

**Implement all four providers:**

**LM Studio** — Uses the OpenAI-compatible REST API. Send a POST to `{lmstudio_base_url}/chat/completions` with the sentiment prompt. No auth header needed.

**Google Gemini** — Use `google-generativeai` SDK. Model: `settings.llm_model` (default `gemini-2.0-flash`, free tier). Use `generate_content` with JSON mode where available.

**OpenRouter** — OpenAI-compatible API at `https://openrouter.ai/api/v1`. Auth header: `Authorization: Bearer {openrouter_api_key}`. Set `HTTP-Referer` header to `http://localhost` and `X-Title` to `SP500NewsCurator`.

**Anthropic** — Use `anthropic` SDK. Messages API. System prompt sets the persona; user message contains the article.

**Shared prompt template** (use for all providers):

```
System: You are a financial analyst AI. Analyze news articles for their potential 
impact on S&P 500 stock prices. Always respond with valid JSON only — no prose, 
no markdown, no explanation outside the JSON object.

User: Analyze this article and respond with exactly this JSON structure:
{
  "sentiment": "bullish" | "bearish" | "neutral",
  "confidence": <float 0.0-1.0>,
  "impact": "high" | "medium" | "low",
  "impact_reason": "<one sentence>",
  "affected_tickers": ["TICKER", ...],
  "affected_sectors": ["Sector", ...],
  "time_horizon": "immediate" | "short_term" | "long_term",
  "summary": "<2 sentence plain English summary for investors>"
}

Rules:
- impact=high means this could move a stock >2% at open
- Only list tickers directly and materially affected
- confidence reflects how clearly bullish or bearish the signal is
- If genuinely market-neutral, sentiment=neutral with confidence>0.8

Headline: {headline}

Body: {body}
```

**Error handling:** If the LLM returns malformed JSON, attempt one retry with an explicit "respond only with valid JSON" reminder appended. If the second attempt also fails, return `None` — the pipeline will fall back to FinBERT-only scoring.

**Timeout:** Wrap all provider calls with `asyncio.wait_for(..., timeout=settings.llm_timeout_seconds)`.

---

## Step 7 — Sentiment Pipeline (`backend/analysis/sentiment_pipeline.py`)

Orchestrates the two-stage pipeline:

```python
async def process_article(article: Article) -> ScoredArticle:
    # Stage 1: FinBERT on headline (fast, free, local)
    finbert_result = await run_finbert(article.headline)

    # Stage 2: Skip LLM if FinBERT is very confident it's neutral
    if finbert_result.neutral > settings.finbert_neutral_threshold:
        return build_scored_article(article, finbert_result, source="finbert")

    # Stage 3: LLM deep analysis
    body_truncated = article.body[:settings.max_article_body_chars]
    llm_result = await score_with_llm(article.headline, body_truncated)

    if llm_result is None:
        # LLM failed — fall back to FinBERT
        return build_scored_article(article, finbert_result, source="finbert_fallback")

    return build_scored_article(article, llm_result, source="llm",
                                llm_provider=settings.llm_provider)
```

Also implement `async def process_batch(articles: list[Article]) -> list[ScoredArticle]` that runs articles concurrently with `asyncio.gather`, limited to 5 concurrent LLM calls via a semaphore (to avoid rate limiting).

---

## Step 8 — Ticker Mapper (`backend/analysis/ticker_mapper.py`)

Build a module that:
1. Maintains a hardcoded dict of all S&P 500 tickers mapped to their company names and GICS sectors
2. Scans article text (headline + body) for ticker mentions (e.g. `$AAPL`, `AAPL`) and company name mentions (e.g. "Apple", "Apple Inc")
3. Returns a list of matched tickers and their sectors
4. Used as a fallback/supplement to the LLM's `affected_tickers` output

Include at minimum the top 50 S&P 500 companies by market cap with their common name aliases (e.g. "Apple" → AAPL, "Microsoft" → MSFT, "Alphabet" / "Google" → GOOGL, etc.)

---

## Step 9 — News Ingestion (`backend/ingestion/`)

**scheduler.py** — Use APScheduler with an AsyncIOScheduler. Register two jobs:
- `ingest_all_sources()` — runs every `settings.ingest_interval_minutes` minutes
- `process_unscored_articles()` — runs every 5 minutes, picks up any articles that failed scoring

**news_api.py** — Fetch from `https://newsapi.org/v2/everything` with queries: `"S&P 500"`, `"stock market"`, `"earnings"`, `"Federal Reserve"`. Deduplicate by `source_url`. Only store articles not already in DB.

**rss_feeds.py** — Parse RSS feeds using `feedparser`:
- Reuters Business: `https://feeds.reuters.com/reuters/businessNews`
- AP Markets: `https://rsshub.app/apnews/topics/financial-markets`
- Yahoo Finance: `https://finance.yahoo.com/rss/`

**sec_edgar.py** — Poll SEC EDGAR company search RSS for S&P 500 companies' 8-K and 10-Q filings:
`https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&dateb=&owner=include&count=20&search_text=&output=atom`

All ingestion functions must:
- Be idempotent (safe to run multiple times, no duplicate articles)
- Log source, count ingested, count skipped (already existed)
- Catch all exceptions and log them — never crash the scheduler

---

## Step 10 — FastAPI Routes (`backend/api/routes/`)

**GET /health** — returns `{status: "ok", llm_provider: "...", finbert_loaded: bool}`

**GET /health/llm** — sends a test prompt to the configured LLM provider, returns `{ok: bool, latency_ms: int, provider: str, model: str, error: str | null}`

**GET /articles**
- Query params: `ticker` (optional), `sector` (optional), `sentiment` (optional: bullish/bearish/neutral), `impact` (optional: high/medium/low), `hours` (default 24), `limit` (default 50, max 200), `offset` (default 0)
- Returns paginated list of articles joined with their scored_article

**GET /articles/{id}** — full article detail including scoring breakdown

**GET /sentiment/ticker/{ticker}**
- Query param: `hours` (default 168 = 7 days)
- Returns: `{ticker, sentiment_trend: [{hour, bullish_count, bearish_count, neutral_count, avg_confidence}], latest_articles: [...]}`

**GET /sentiment/sectors**
- Returns current sentiment summary grouped by GICS sector

**GET /watchlist** — list all watchlist items

**POST /watchlist** — add ticker `{ticker: str, alert_threshold: str}`

**DELETE /watchlist/{ticker}** — remove ticker

**POST /ingest/trigger** — manually trigger ingestion (for dev/testing)

All routes must use async SQLAlchemy sessions. Use `Depends()` for DB session injection.

---

## Step 11 — Frontend (`frontend/src/`)

Stack: React 18, TypeScript, Vite, Tailwind CSS, Recharts, React Query (TanStack Query), Axios.

**Dashboard page** layout — three-column grid on desktop, stacked on mobile:

Left column: `TickerFilter` — checklist of all S&P 500 tickers the user can filter by. Pre-populate from watchlist. Search/filter input at top.

Center column: `NewsFeed` — infinite scroll list of articles. Each card shows:
- Headline (linked to source URL)
- Source name + published time (relative: "2h ago")
- `ImpactBadge` — colored pill: HIGH (red), MEDIUM (amber), LOW (gray)
- Sentiment indicator: bull/bear/neutral icon + confidence %
- AI summary (collapsed by default, expand on click)
- Affected tickers as clickable pills

Right column: `SentimentChart` — line chart (Recharts) showing bullish vs bearish article counts over the last 7 days for the selected ticker. Defaults to overall S&P 500.

**Watchlist panel** — collapsible sidebar showing watched tickers with their current 24h sentiment summary. Click a ticker to filter the feed.

**Settings page** — read-only display of current LLM provider, model, and FinBERT status fetched from `/health`.

**Auto-refresh:** Use React Query's `refetchInterval: 60000` (1 minute) for the news feed and sentiment chart.

---

## Step 12 — Nginx Config

```nginx
server {
    listen 80;

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }

    location / {
        proxy_pass http://frontend:5173;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Step 13 — Backend `requirements.txt`

Include exact or minimum versions:

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic-settings>=2.0.0
apscheduler>=3.10.0
httpx>=0.27.0
feedparser>=6.0.11
transformers>=4.40.0
torch>=2.0.0
python-dotenv>=1.0.0
google-generativeai>=0.7.0
anthropic>=0.28.0
openai>=1.30.0
redis[asyncio]>=5.0.0
newsapi-python>=0.2.7
python-multipart>=0.0.9
```

---

## Step 14 — Backend `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System deps for torch + transformers
RUN apt-get update && apt-get install -y \
    gcc g++ curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download FinBERT weights at build time so first startup is instant
# This bakes the model into the image layer — cached across rebuilds
RUN python -c "from transformers import pipeline; \
    pipeline('text-classification', model='ProsusAI/finbert', \
    cache_dir='/app/model_cache')"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Step 15 — Frontend `Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## Step 16 — `.env.example`

```bash
# ── Database ────────────────────────────────────────────
POSTGRES_DB=sp500news
POSTGRES_USER=newsuser
POSTGRES_PASSWORD=changeme
DATABASE_URL=postgresql+asyncpg://newsuser:changeme@postgres:5432/sp500news

# ── Redis ───────────────────────────────────────────────
REDIS_URL=redis://redis:6379

# ── LLM Provider ────────────────────────────────────────
# Options: lmstudio | gemini | openrouter | anthropic
LLM_PROVIDER=lmstudio
LLM_MODEL=mistral

# ── LM Studio (local) ───────────────────────────────────
# Set this to your LM Studio server address
# From inside Docker, use host.docker.internal to reach your host machine
LMSTUDIO_BASE_URL=http://host.docker.internal:1234/v1

# ── Google Gemini (free tier available) ─────────────────
# Get key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=

# ── OpenRouter (access to 100+ models) ──────────────────
# Get key at: https://openrouter.ai/keys
# Set LLM_MODEL to e.g. mistralai/mistral-7b-instruct:free
OPENROUTER_API_KEY=

# ── Anthropic Claude ────────────────────────────────────
# Get key at: https://console.anthropic.com/
# Set LLM_MODEL to e.g. claude-haiku-4-5-20251001
ANTHROPIC_API_KEY=

# ── News Sources ─────────────────────────────────────────
# Get free key at: https://newsapi.org/register
NEWSAPI_KEY=

# ── Pipeline Tuning ──────────────────────────────────────
INGEST_INTERVAL_MINUTES=30
MAX_CONCURRENT_LLM_CALLS=1
FINBERT_NEUTRAL_THRESHOLD=0.85
MAX_ARTICLE_BODY_CHARS=3000
LLM_TIMEOUT_SECONDS=30
```

**Rate Limit Guidance:**
- **Gemini (free tier):** ~15–30 RPM limit using `gemini-2.0-flash`. Set `MAX_CONCURRENT_LLM_CALLS=1` to stay well within limits.
- **Other providers:** Check rate limits in their dashboards; adjust `MAX_CONCURRENT_LLM_CALLS` accordingly.
- **LM Studio:** No external rate limits (runs locally).

---

## Step 17 — README.md

Write a clear `README.md` at project root covering:

1. **Prerequisites** — Docker Desktop, optionally LM Studio or API keys
2. **Quick start** (5 commands: clone, copy .env.example, configure one provider, docker-compose up, open browser)
3. **LLM provider setup guide** — one section per provider with exact steps:
   - LM Studio: download, load a model, enable server, no key needed
   - Gemini: link to key page, set `LLM_PROVIDER=gemini`, set `GEMINI_API_KEY`, set `LLM_MODEL=gemini-2.0-flash`
   - OpenRouter: link to key page, set provider + key + model (list 3 free model examples)
   - Anthropic: link to console, set provider + key + model
4. **Architecture overview** — brief description of each service
5. **API reference** — list of all endpoints with example curl commands
6. **Development tips** — how to trigger manual ingestion, view logs per service, access the DB

---

## Coding Standards

Apply these rules to every file you create:

- **Python:** async/await throughout. Type hints on all functions. Pydantic models for all API request/response bodies. Structured logging via Python `logging` module (not print). Docstrings on all classes and public functions.

- **TypeScript/React:** Functional components only. React Query for all server state. No `any` types — define interfaces for all API responses. Tailwind utility classes only — no custom CSS files.

- **Error handling:** Every external call (HTTP, DB, model inference) wrapped in try/except or .catch(). Errors logged with context (which article, which provider, what failed). API routes return proper HTTP status codes (404, 422, 503) not always 500.

- **Security:** No secrets hardcoded anywhere. All config from environment. CORS configured to allow `http://localhost:5173` and `http://localhost` in dev.

---

## Build Order

Execute in this exact order:

1. Create directory structure and `.gitignore`
2. Write `docker-compose.yml`
3. Write `.env.example`
4. Write `backend/config.py`
5. Write `backend/db/models.py` and `backend/db/database.py`
6. Run Alembic init and create initial migration
7. Write `backend/analysis/finbert.py`
8. Write `backend/analysis/llm_client.py` (all 4 providers)
9. Write `backend/analysis/sentiment_pipeline.py`
10. Write `backend/analysis/ticker_mapper.py`
11. Write `backend/ingestion/` modules
12. Write `backend/api/routes/` modules
13. Write `backend/main.py` (wire everything together)
14. Write `backend/Dockerfile` and `backend/requirements.txt`
15. Scaffold frontend with Vite + React + TypeScript + Tailwind
16. Write frontend components and pages
17. Write `frontend/Dockerfile`
18. Write `nginx/nginx.conf`
19. Write `README.md`
20. Final check: verify all imports resolve, all env vars are in `.env.example`, all docker-compose services have healthchecks

---

## Verification Checklist

Before declaring done, confirm:

- [ ] `docker-compose up --build` completes without errors
- [ ] `GET /health` returns 200 with correct provider name
- [ ] `GET /health/llm` returns a response (ok=true or ok=false with error message — not a 500)
- [ ] `POST /ingest/trigger` returns 200 and articles appear in DB
- [ ] `GET /articles` returns paginated results
- [ ] Frontend loads at `http://localhost` with no console errors
- [ ] Switching `LLM_PROVIDER` in `.env` and restarting backend changes provider with no code changes
- [ ] FinBERT model loads from cache on second startup (not re-downloaded)
- [ ] All four LLM providers have code paths (even if only one is tested)
