import asyncio
import math
import os
import time
import requests
import yfinance as yf
import difflib
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

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


def _clean_float(val):
    """Returns None for NaN/invalid floats, since JSON cannot serialize NaN."""
    if val is None:
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _fetch_finnhub_overview(ticker: str) -> dict:
    """
    Primary fallback for market cap / P-E ratio. Finnhub's free tier
    (60 req/min) is far more generous than Alpha Vantage's (25/day),
    so it's much less likely to be exhausted by shared-IP hosting.
    Strips exchange suffixes since Finnhub's free tier is US-focused.
    """
    if not FINNHUB_API_KEY:
        print("[DEBUG] No FINNHUB_API_KEY set, skipping Finnhub fallback")
        return {"current_price": None, "market_cap": None, "pe_ratio": None}

    symbol = ticker.split(".")[0]

    try:
        profile_resp = requests.get(
            "https://finnhub.io/api/v1/stock/profile2",
            params={"symbol": symbol, "token": FINNHUB_API_KEY},
            timeout=10,
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        metric_resp = requests.get(
            "https://finnhub.io/api/v1/stock/metric",
            params={"symbol": symbol, "metric": "all", "token": FINNHUB_API_KEY},
            timeout=10,
        )
        metric_resp.raise_for_status()
        metrics = metric_resp.json().get("metric", {})

        market_cap = profile.get("marketCapitalization")
        # Finnhub returns market cap in millions
        market_cap = _clean_float(market_cap) * 1_000_000 if market_cap else None
        pe_ratio = _clean_float(metrics.get("peTTM") or metrics.get("peBasicExclExtraTTM"))

        if market_cap is None and pe_ratio is None:
            print(f"[DEBUG] Finnhub returned no usable data for {symbol}")
            return {"current_price": None, "market_cap": None, "pe_ratio": None}

        print(f"[DEBUG] Finnhub overview succeeded for {symbol}")
        return {"current_price": None, "market_cap": market_cap, "pe_ratio": pe_ratio}

    except Exception as e:
        print(f"[DEBUG] Finnhub fallback failed for {symbol}: {e}")
        return {"current_price": None, "market_cap": None, "pe_ratio": None}


def _fetch_alpha_vantage_overview(ticker: str) -> dict:
    """Secondary fallback if Finnhub also fails to provide data."""
    if not ALPHA_VANTAGE_API_KEY:
        return {"current_price": None, "market_cap": None, "pe_ratio": None}

    symbol = ticker.split(".")[0]

    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "OVERVIEW", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data or "MarketCapitalization" not in data:
            print(f"[DEBUG] Alpha Vantage returned no overview data for {symbol}")
            return {"current_price": None, "market_cap": None, "pe_ratio": None}

        print(f"[DEBUG] Alpha Vantage overview succeeded for {symbol}")
        return {
            "current_price": None,
            "market_cap": _clean_float(data.get("MarketCapitalization")),
            "pe_ratio": _clean_float(data.get("PERatio")),
        }

    except Exception as e:
        print(f"[DEBUG] Alpha Vantage fallback failed for {symbol}: {e}")
        return {"current_price": None, "market_cap": None, "pe_ratio": None}


def _fetch_info_with_retry(stock: yf.Ticker, ticker: str, max_retries: int = 3) -> dict:
    for attempt in range(1, max_retries + 1):
        try:
            info = stock.info
            if info and (info.get("currentPrice") is not None or info.get("marketCap") is not None):
                print(f"[DEBUG] .info succeeded for {ticker} on attempt {attempt}")
                return {
                    "current_price": _clean_float(info.get("currentPrice")),
                    "market_cap": _clean_float(info.get("marketCap")),
                    "pe_ratio": _clean_float(info.get("trailingPE")),
                }
            raise ValueError("Empty or incomplete info returned")
        except Exception as e:
            print(f"[DEBUG] .info attempt {attempt} failed for {ticker}: {e}")
            if attempt < max_retries:
                time.sleep(1.0 * attempt)

    print(f"[DEBUG] All .info attempts failed for {ticker}, trying Finnhub fallback")
    finnhub_data = _fetch_finnhub_overview(ticker)

    if finnhub_data["market_cap"] is not None or finnhub_data["pe_ratio"] is not None:
        return finnhub_data

    print(f"[DEBUG] Finnhub had no data for {ticker}, trying Alpha Vantage fallback")
    return _fetch_alpha_vantage_overview(ticker)


def _fetch_sync(ticker: str, max_retries: int = 3) -> dict:
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")

            if hist is None or hist.empty:
                raise ValueError("Empty history returned")

            print(f"[DEBUG] Ticker: {ticker}, attempt {attempt}, rows fetched: {len(hist)}")

            history = []
            skipped = 0
            for idx, row in hist.iterrows():
                close_val = _clean_float(row["Close"])
                if close_val is None:
                    skipped += 1
                    continue
                history.append({"date": str(idx.date()), "close": round(close_val, 2)})

            if skipped:
                print(f"[DEBUG] Skipped {skipped} row(s) with invalid/NaN close price for {ticker}")

            if not history:
                raise ValueError("All rows had invalid close prices")

            info_data = _fetch_info_with_retry(stock, ticker)

            current_price = info_data["current_price"]
            if current_price is None and history:
                current_price = history[-1]["close"]

            return {
                "history": history,
                "current_price": current_price,
                "market_cap": info_data["market_cap"],
                "pe_ratio": info_data["pe_ratio"],
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
