import asyncio
import requests
import yfinance as yf
import difflib

# Known company name -> ticker mappings, checked first before any API search.
# Add more entries here as you demo different companies.
KNOWN_TICKERS = {
    "mrf": "MRF.NS",
    "tcs": "TCS.NS",
    "tata consultancy services": "TCS.NS",
    "infosys": "INFY.NS",
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "wipro": "WIPRO.NS",
    "tata motors": "TATAMOTORS.NS",
    "adani enterprises": "ADANIENT.NS",
    "amazon": "AMZN",
    "apple": "AAPL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "nvidia": "NVDA",
}


def _fetch_sync(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    hist = stock.history(period="3mo")
    print(f"[DEBUG] Ticker: {ticker}, rows fetched: {len(hist)}")

    history = [
        {"date": str(idx.date()), "close": round(row["Close"], 2)}
        for idx, row in hist.iterrows()
    ]

    info = stock.info

    return {
        "history": history,
        "current_price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
    }


async def get_market_data(ticker: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync, ticker)


def _resolve_ticker_sync(query: str, exchange: str = "NSE") -> str:
    query_clean = query.strip().lower()

    # 1. Check the known-tickers lookup table first — fastest and most reliable
    if query_clean in KNOWN_TICKERS:
        return KNOWN_TICKERS[query_clean]

    # 1b. Catch typos (e.g. "nividia" -> "nvidia") via fuzzy matching
    close_matches = difflib.get_close_matches(query_clean, KNOWN_TICKERS.keys(), n=1, cutoff=0.75)
    if close_matches:
        return KNOWN_TICKERS[close_matches[0]]

    query_upper = query.strip().upper()

    # 2. If it already looks like a valid ticker, verify it directly with yfinance
    if len(query_upper) <= 12 and ("." in query_upper or " " not in query_upper):
        suffix_map = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": ""}
        suffix = suffix_map.get(exchange, "")

        # Try the exchange-specific version first (e.g. INFY -> INFY.NS for NSE)
        if suffix and not query_upper.endswith(suffix):
            candidate = f"{query_upper}{suffix}"
            try:
                test = yf.Ticker(candidate)
                if test.history(period="5d").shape[0] > 0:
                    return candidate
            except Exception:
                pass

        # Fall back to the bare ticker as typed
        try:
            test = yf.Ticker(query_upper)
            if test.history(period="5d").shape[0] > 0:
                return query_upper
        except Exception:
            pass

    # 3. Fall back to Yahoo Finance's search, filtered to equities only
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {"q": query, "quotesCount": 10, "newsCount": 0}
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        quotes = data.get("quotes", [])
        equities = [q for q in quotes if q.get("quoteType") == "EQUITY"]

        if not equities:
            return query

        suffix_map = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": ""}
        preferred_suffix = suffix_map.get(exchange, "")

        for q in equities:
            symbol = q.get("symbol", "")
            if preferred_suffix and symbol.endswith(preferred_suffix):
                return symbol

        return equities[0].get("symbol", query)

    except Exception:
        return query


async def resolve_ticker(query: str, exchange: str = "NSE") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _resolve_ticker_sync, query, exchange)

