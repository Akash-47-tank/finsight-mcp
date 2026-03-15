"""
Tool: search_news
Searches for recent financial news using NewsAPI.org free tier.
Falls back to yfinance .news property if NewsAPI key is not set.

Free tier: 100 requests/day — sufficient for demo purposes.
Sign up at: https://newsapi.org/register (free account)
"""

import os
import json
from typing import Any
from datetime import datetime, timedelta

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

import yfinance as yf


def search_news(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Search for financial news articles.

    Args:
        query: Search string e.g. 'Reliance Industries Q3 results'
        max_results: How many articles to return (1-5)

    Returns:
        dict with list of articles (title, description, url, published_at, source)
    """
    max_results = min(max(1, max_results), 5)  # clamp between 1-5
    api_key = os.getenv("NEWS_API_KEY", "")

    if api_key and HTTPX_AVAILABLE:
        return _fetch_from_newsapi(query, max_results, api_key)
    else:
        # Fallback: use yfinance ticker news (works without API key)
        return _fetch_from_yfinance(query, max_results)


def _fetch_from_newsapi(query: str, max_results: int, api_key: str) -> dict[str, Any]:
    """Fetch from NewsAPI.org free tier."""
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q":        query + " India stock market",
        "from":     from_date,
        "sortBy":   "publishedAt",
        "language": "en",
        "pageSize": max_results,
        "apiKey":   api_key
    }

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    articles = []
    for item in data.get("articles", [])[:max_results]:
        articles.append({
            "title":        item.get("title", "N/A"),
            "description":  item.get("description", "No description available"),
            "url":          item.get("url", ""),
            "source":       item.get("source", {}).get("name", "Unknown"),
            "published_at": item.get("publishedAt", "")[:10]   # date only
        })

    return {
        "query":    query,
        "source":   "NewsAPI",
        "count":    len(articles),
        "articles": articles,
        "status":   "success"
    }


def _fetch_from_yfinance(query: str, max_results: int) -> dict[str, Any]:
    """
    Fallback: extract ticker from query and use yfinance's built-in news feed.
    Works without any API key.
    """
    # Try to guess ticker from common company names in query
    name_to_ticker = {
        "reliance":   "RELIANCE.NS",
        "tcs":        "TCS.NS",
        "infosys":    "INFY.NS",
        "wipro":      "WIPRO.NS",
        "hdfc":       "HDFCBANK.NS",
        "icici":      "ICICIBANK.NS",
        "sbi":        "SBIN.NS",
        "itc":        "ITC.NS",
        "bajaj":      "BAJFINANCE.NS",
        "kotak":      "KOTAKBANK.NS",
        "axis":       "AXISBANK.NS",
        "maruti":     "MARUTI.NS",
        "tatamotors": "TATAMOTORS.NS",
        "tata":       "TCS.NS",
        "adani":      "ADANIENT.NS",
        "nifty":      "^NSEI",
        "sensex":     "^BSESN",
    }

    ticker_sym = "RELIANCE.NS"  # default fallback
    query_lower = query.lower()
    for keyword, sym in name_to_ticker.items():
        if keyword in query_lower:
            ticker_sym = sym
            break

    stock = yf.Ticker(ticker_sym)
    raw_news = stock.news or []

    articles = []
    for item in raw_news[:max_results]:
        content = item.get("content", {})
        articles.append({
            "title":        content.get("title", item.get("title", "N/A")),
            "description":  content.get("summary", item.get("summary", "No summary available")),
            "url":          content.get("canonicalUrl", {}).get("url", ""),
            "source":       content.get("provider", {}).get("displayName", "Yahoo Finance"),
            "published_at": content.get("pubDate", "")[:10] if content.get("pubDate") else ""
        })

    return {
        "query":    query,
        "source":   "yfinance (fallback — set NEWS_API_KEY for better results)",
        "count":    len(articles),
        "articles": articles,
        "status":   "success"
    }
