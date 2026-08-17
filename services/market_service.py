import asyncio
import time
import requests
import yfinance as yf
import difflib

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


def _fetch_sync(ticker: str, max_retries: int = 3) -> dict:
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")

            if hist is None or hist.empty:
                raise ValueError("Empty history returned")

            print(f"[DEBUG] Ticker: {ticker}, attempt {attempt}, rows fetched: {len(hist)}")

            history = [
                {"date": str(idx.date()), "close": round(row["Close"], 2)}
                for idx, row in hist.iterrows()
            ]

            current_price = None
            market_cap = None
            pe_ratio = None
            try:
                info = stock.info
                current_price = info.get("currentPrice")
                market_cap = info.get("marketCap")
                pe_ratio = info.get("trailingPE")
            except Exception as e:
                print(f"[DEBUG] .info fetch failed for {ticker}: {e}")

            if current_price is None and history:
                current_price = history[-1]["close"]

            return {
                "history": history,
                "current_price": current_price,
                "market_cap": market_cap,
                "pe_ratio": pe_ratio,
            }

        except Exception as e:
            last_error = e
            print(f"[DEBUG] Attempt {attempt} failed for {ticker}: {e}")
            if attempt < max_retries:
                time.sleep(1.5 * attempt)

    print(f"[DEBUG] All {max_retries} attempts failed for {ticker}. Last error: {last_error}")
    return {"history": [], "current_price": None, "market_cap": None, "pe_ratio": None}


async def get_market_data(ticker: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_sync, ticker)


def _resolve_ticker_sync(query: str, exchange: str = "NSE") -> str:
    query_clean = query.strip().lower()

    if query_clean in KNOWN_TICKERS:
        return KNOWN_TICKERS[query_clean]

    close_matches = difflib.get_close_matches(query_clean, KNOWN_TICKERS.keys(), n=1, cutoff=0.75)
    if close_matches:
        return KNOWN_TICKERS[close_matches[0]]

    query_upper = query.strip().upper()

    if len(query_upper) <= 12 and ("." in query_upper or " " not in query_upper):
        suffix_map = {"NSE": ".NS", "BSE": ".BO", "NASDAQ": ""}
        suffix = suffix_map.get(exchange, "")

        if suffix and not query_upper.endswith(suffix):
            candidate = f"{query_upper}{suffix}"
            try:
                test = yf.Ticker(candidate)
                if test.history(period="5d").shape[0] > 0:
                    return candidate
            except Exception:
                pass

        try:
            test = yf.Ticker(query_upper)
            if test.history(period="5d").shape[0] > 0:
                return query_upper
        except Exception:
            pass

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
