# S&P 500 News Curator — Feature Expansion Design

## Overview

Three-phase feature expansion:
- **Phase 1:** Earnings calendar, economic indicators, historical sentiment tracking
- **Phase 2:** Alert/notification system (in-app, email via Gmail SMTP, web push)
- **Phase 3:** SEC 13F filings, Fed calendar/FOMC

UI polish after all three phases.

---

## Phase 1: Data & History Foundation

### New Data Sources

**Earnings Calendar (yfinance)**
- Library: yfinance Python package
- Scheduled: daily via APScheduler
- Stores earnings_reports table
- Covers all watched tickers + top S&P 500
- Fields: ticker, fiscal_quarter, eps_estimate, eps_actual, revenue_estimate, revenue_actual, report_date, report_time (bmo/amc)

**Economic Indicators (fredapi)**
- Library: redapi Python package
- Requires FRED API key in .env: FRED_API_KEY=...
- Scheduled: daily via APScheduler
- Stores economic_indicators table
- Indicators: CPI, Nonfarm Payrolls, Fed Funds Rate, Unemployment Rate, GDP

### Historical Sentiment Tracking

New sentiment_history table: id, ticker, date, bullish_count, bearish_count, neutral_count, total_articles, avg_confidence, composite_score, created_at
Unique constraint: (ticker, date). Daily aggregation job at 00:30.

### New API Endpoints

`
GET  /sentiment/history/{ticker}?days=7|30|90
GET  /indicators?names=cpi,payems&days=90
GET  /earnings?ticker=AAPL&upcoming=true&days=30
`

### Frontend Additions

1. Sentiment trend chart overhaul: 7d/30d/90d tabs, 3-series line chart
2. Economic indicators panel: collapsible, sparklines, color-coded
3. Earnings calendar widget: upcoming earnings for watched tickers

### New Dependencies: yfinance, fredapi

---

## Phase 2: Alert System

### Database Tables

- lert_rules: id, ticker (nullable), rule_type, threshold, channel, enabled, last_triggered_at, created_at
- 
otifications: id, alert_rule_id (FK), title, body, ticker, notification_type, channel, status, read_at, sent_at, created_at
- push_subscriptions: id, endpoint, p256dh_key, auth_key, created_at

### Alert Rule Types

| Rule Type | Condition |
|-----------|-----------|
| sentiment_shift | Composite score shifts by X over 24h |
| impact_threshold | Article impact >= X for watched ticker |
| earnings | Earnings published for watched ticker |
| economic | Economic indicator deviates by X% |

### Email (Gmail SMTP)

smtplib + starttls + HTML template. Requires Gmail app password.

### API Endpoints

`
GET/POST/PUT/DELETE /alerts/rules
GET /alerts/notifications
PUT /alerts/notifications/{id}/read
POST /alerts/notifications/read-all
POST/DELETE /alerts/push/subscribe
`

### Frontend Additions

- Notification bell in header with badge + dropdown
- Alert rules CRUD page (/alerts)
- Settings additions for email/push config

### New Dependencies: pywebpush

---

## Phase 3: More Data Sources

### SEC 13F Filings
- Table: sec_13f_filings (ticker, cik, filing_date, period_date, shares_held, value)
- Weekly check, reuse SEC EDGAR infra
- Frontend: Whales panel

### Fed Calendar / FOMC
- Table: fed_events (event_name, event_date, event_type, actual_rate, expected_rate)
- Weekly check
- Frontend: Fed calendar timeline widget

### Earnings Pass
- Enrich earnings_reports with surprise_percent, revenue_estimate, revenue_actual

---

## Implementation Order: Phase 1 -> Phase 2 -> Phase 3 -> UI Polish

## Design Decisions

1. Start fresh on sentiment_history (no backfill)
2. Skip Twitter/X
3. Gmail SMTP for email alerts
4. pywebpush for web push
5. Single-user (global rules/notifications)
6. FRED API for economic indicators
7. yfinance for earnings data
