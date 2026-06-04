"""Ticker mapper — maps article text to S&P 500 tickers and GICS sectors.

Maintains a hardcoded dictionary of top 50 S&P 500 companies by market cap
with common name aliases. Scans text for ticker symbols ($AAPL, AAPL) and
company name mentions.
"""

import re
from typing import TypedDict

class TickerMatch(TypedDict):
    ticker: str
    company: str
    sector: str


# Top 50 S&P 500 companies by market cap with aliases
SP500_TOP50: dict[str, dict] = {
    "AAPL":  {"company": "Apple Inc", "aliases": ["Apple"], "sector": "Information Technology"},
    "MSFT":  {"company": "Microsoft Corporation", "aliases": ["Microsoft"], "sector": "Information Technology"},
    "GOOGL": {"company": "Alphabet Inc", "aliases": ["Alphabet", "Google"], "sector": "Communication Services"},
    "GOOG":  {"company": "Alphabet Inc", "aliases": [], "sector": "Communication Services"},
    "AMZN":  {"company": "Amazon.com Inc", "aliases": ["Amazon"], "sector": "Consumer Discretionary"},
    "NVDA":  {"company": "NVIDIA Corporation", "aliases": ["NVIDIA", "Nvidia"], "sector": "Information Technology"},
    "META":  {"company": "Meta Platforms Inc", "aliases": ["Meta", "Facebook"], "sector": "Communication Services"},
    "TSLA":  {"company": "Tesla Inc", "aliases": ["Tesla"], "sector": "Consumer Discretionary"},
    "BRK.B": {"company": "Berkshire Hathaway", "aliases": ["Berkshire"], "sector": "Financials"},
    "JPM":   {"company": "JPMorgan Chase & Co", "aliases": ["JPMorgan", "JP Morgan", "Chase"], "sector": "Financials"},
    "JNJ":   {"company": "Johnson & Johnson", "aliases": ["J&J"], "sector": "Health Care"},
    "UNH":   {"company": "UnitedHealth Group", "aliases": ["UnitedHealth", "United Health"], "sector": "Health Care"},
    "V":     {"company": "Visa Inc", "aliases": ["Visa"], "sector": "Financials"},
    "XOM":   {"company": "Exxon Mobil Corporation", "aliases": ["Exxon", "ExxonMobil", "Exxon Mobil"], "sector": "Energy"},
    "MA":    {"company": "Mastercard Incorporated", "aliases": ["Mastercard"], "sector": "Financials"},
    "PG":    {"company": "Procter & Gamble", "aliases": ["Procter and Gamble", "P&G"], "sector": "Consumer Staples"},
    "HD":    {"company": "The Home Depot", "aliases": ["Home Depot"], "sector": "Consumer Discretionary"},
    "CVX":   {"company": "Chevron Corporation", "aliases": ["Chevron"], "sector": "Energy"},
    "LLY":   {"company": "Eli Lilly and Company", "aliases": ["Eli Lilly", "Lilly"], "sector": "Health Care"},
    "ABBV":  {"company": "AbbVie Inc", "aliases": ["AbbVie"], "sector": "Health Care"},
    "MRK":   {"company": "Merck & Co", "aliases": ["Merck"], "sector": "Health Care"},
    "PEP":   {"company": "PepsiCo Inc", "aliases": ["PepsiCo", "Pepsi"], "sector": "Consumer Staples"},
    "KO":    {"company": "The Coca-Cola Company", "aliases": ["Coca-Cola", "Coke"], "sector": "Consumer Staples"},
    "AVGO":  {"company": "Broadcom Inc", "aliases": ["Broadcom"], "sector": "Information Technology"},
    "COST":  {"company": "Costco Wholesale", "aliases": ["Costco"], "sector": "Consumer Staples"},
    "TMO":   {"company": "Thermo Fisher Scientific", "aliases": ["Thermo Fisher"], "sector": "Health Care"},
    "WMT":   {"company": "Walmart Inc", "aliases": ["Walmart"], "sector": "Consumer Staples"},
    "CSCO":  {"company": "Cisco Systems", "aliases": ["Cisco"], "sector": "Information Technology"},
    "MCD":   {"company": "McDonald's Corporation", "aliases": ["McDonald's", "McDonalds"], "sector": "Consumer Discretionary"},
    "CRM":   {"company": "Salesforce Inc", "aliases": ["Salesforce"], "sector": "Information Technology"},
    "ACN":   {"company": "Accenture plc", "aliases": ["Accenture"], "sector": "Information Technology"},
    "LIN":   {"company": "Linde plc", "aliases": ["Linde"], "sector": "Materials"},
    "ABT":   {"company": "Abbott Laboratories", "aliases": ["Abbott"], "sector": "Health Care"},
    "ADBE":  {"company": "Adobe Inc", "aliases": ["Adobe"], "sector": "Information Technology"},
    "AMD":   {"company": "Advanced Micro Devices", "aliases": ["AMD"], "sector": "Information Technology"},
    "ORCL":  {"company": "Oracle Corporation", "aliases": ["Oracle"], "sector": "Information Technology"},
    "NFLX":  {"company": "Netflix Inc", "aliases": ["Netflix"], "sector": "Communication Services"},
    "NKE":   {"company": "NIKE Inc", "aliases": ["Nike"], "sector": "Consumer Discretionary"},
    "TXN":   {"company": "Texas Instruments", "aliases": ["Texas Instruments", "TI"], "sector": "Information Technology"},
    "DHR":   {"company": "Danaher Corporation", "aliases": ["Danaher"], "sector": "Health Care"},
    "INTC":  {"company": "Intel Corporation", "aliases": ["Intel"], "sector": "Information Technology"},
    "PM":    {"company": "Philip Morris International", "aliases": ["Philip Morris"], "sector": "Consumer Staples"},
    "DIS":   {"company": "The Walt Disney Company", "aliases": ["Disney", "Walt Disney"], "sector": "Communication Services"},
    "QCOM":  {"company": "Qualcomm Incorporated", "aliases": ["Qualcomm"], "sector": "Information Technology"},
    "CMCSA": {"company": "Comcast Corporation", "aliases": ["Comcast"], "sector": "Communication Services"},
    "VZ":    {"company": "Verizon Communications", "aliases": ["Verizon"], "sector": "Communication Services"},
    "NEE":   {"company": "NextEra Energy", "aliases": ["NextEra"], "sector": "Utilities"},
    "BA":    {"company": "The Boeing Company", "aliases": ["Boeing"], "sector": "Industrials"},
    "AMGN":  {"company": "Amgen Inc", "aliases": ["Amgen"], "sector": "Health Care"},
    "GS":    {"company": "The Goldman Sachs Group", "aliases": ["Goldman Sachs", "Goldman"], "sector": "Financials"},
}

# Build reverse lookup: alias/company name → ticker
_alias_to_ticker: dict[str, str] = {}
for ticker, info in SP500_TOP50.items():
    _alias_to_ticker[info["company"].lower()] = ticker
    for alias in info["aliases"]:
        _alias_to_ticker[alias.lower()] = ticker

# Sort aliases by length (longest first) to match longer names before shorter ones
_sorted_aliases = sorted(_alias_to_ticker.keys(), key=len, reverse=True)

# Build regex for ticker symbols: $AAPL or standalone AAPL (uppercase, 1-5 chars)
_ticker_pattern = re.compile(r'(?<!\w)\$?(' + '|'.join(re.escape(t) for t in SP500_TOP50.keys()) + r')(?!\w)')


def extract_tickers(text: str) -> list[TickerMatch]:
    """Extract S&P 500 ticker mentions from text.

    Scans for:
    1. Ticker symbols like $AAPL or AAPL
    2. Company name mentions like "Apple" or "Microsoft Corporation"

    Returns deduplicated list of matched tickers with their company names and sectors.
    """
    found: dict[str, TickerMatch] = {}

    # 1. Match ticker symbols
    for match in _ticker_pattern.finditer(text):
        ticker = match.group(1)
        if ticker in SP500_TOP50:
            info = SP500_TOP50[ticker]
            found[ticker] = TickerMatch(ticker=ticker, company=info["company"], sector=info["sector"])

    # 2. Match company names / aliases (case-insensitive)
    text_lower = text.lower()
    for alias in _sorted_aliases:
        if alias in text_lower:
            ticker = _alias_to_ticker[alias]
            if ticker not in found:
                info = SP500_TOP50[ticker]
                found[ticker] = TickerMatch(ticker=ticker, company=info["company"], sector=info["sector"])

    return list(found.values())


def get_sector_for_ticker(ticker: str) -> str | None:
    """Return the GICS sector for a given ticker, or None if not found."""
    info = SP500_TOP50.get(ticker)
    return info["sector"] if info else None
