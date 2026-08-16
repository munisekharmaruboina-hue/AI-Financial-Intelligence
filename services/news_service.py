import asyncio
import requests
import yfinance as yf


def _fetch_news_sync(ticker: str, limit: int = 5) -> list[dict]:
    stock = yf.Ticker(ticker)
    raw_news = stock.news or []

    articles = []
    for item in raw_news[:limit]:
        content = item.get("content", item)
        articles.append({
            "title": content.get("title", ""),
            "summary": content.get("summary", "") or content.get("title", ""),
            "content": content.get("summary", ""),
            "publisher": content.get("provider", {}).get("displayName", "")
                if isinstance(content.get("provider"), dict) else "",
            "link": content.get("canonicalUrl", {}).get("url", "")
                if isinstance(content.get("canonicalUrl"), dict) else "",
        })

    return articles


def _fetch_general_search_news_sync(company_name: str, limit: int = 5) -> list[dict]:
    """
    Fallback: searches Yahoo Finance's general search endpoint for news
    when the ticker-specific .news feed returns nothing. Broader company-name
    based search sometimes surfaces sector or company coverage the direct
    ticker feed misses.
    """
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search"
        params = {"q": company_name, "quotesCount": 0, "newsCount": limit}
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        news_items = data.get("news", [])
        articles = []
        for item in news_items[:limit]:
            articles.append({
                "title": item.get("title", ""),
                "summary": item.get("title", ""),  # search results often lack a full summary
                "content": item.get("title", ""),
                "publisher": item.get("publisher", ""),
                "link": item.get("link", ""),
            })
        return articles

    except Exception:
        return []


async def fetch_latest_news(ticker: str, limit: int = 5) -> list[dict]:
    loop = asyncio.get_event_loop()

    articles = await loop.run_in_executor(None, _fetch_news_sync, ticker, limit)

    if not articles:
        # Fall back to a broader company-name search (strip exchange suffix for a cleaner query)
        company_query = ticker.split(".")[0]
        articles = await loop.run_in_executor(
            None, _fetch_general_search_news_sync, company_query, limit
        )

    return articles