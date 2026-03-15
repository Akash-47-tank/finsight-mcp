"""
Tool: get_stock_price
Fetches current live price and quote data for an Indian (NSE) stock using yfinance.
yfinance is completely free — no API key required.
"""

from typing import Any
import yfinance as yf
from datetime import datetime


def get_stock_price(ticker: str) -> dict[str, Any]:
    """
    Fetch current price data for an NSE-listed stock.

    Args:
        ticker: NSE ticker in Yahoo Finance format e.g. 'TCS.NS', 'RELIANCE.NS'

    Returns:
        dict with current price, change, volume, and exchange info
    """
    # Normalise: if user types 'TCS' without '.NS', add it
    if "." not in ticker:
        ticker = ticker.upper() + ".NS"
    else:
        ticker = ticker.upper()

    stock = yf.Ticker(ticker)
    info  = stock.info

    # yfinance key names can vary; use .get() with fallbacks
    current_price     = info.get("currentPrice") or info.get("regularMarketPrice")
    previous_close    = info.get("previousClose") or info.get("regularMarketPreviousClose")
    open_price        = info.get("open") or info.get("regularMarketOpen")
    day_high          = info.get("dayHigh") or info.get("regularMarketDayHigh")
    day_low           = info.get("dayLow") or info.get("regularMarketDayLow")
    volume            = info.get("volume") or info.get("regularMarketVolume")
    market_cap        = info.get("marketCap")
    company_name      = info.get("longName") or info.get("shortName") or ticker
    currency          = info.get("currency", "INR")
    exchange          = info.get("exchange", "NSI")

    # Calculate price change
    price_change      = None
    price_change_pct  = None
    if current_price and previous_close:
        price_change     = round(current_price - previous_close, 2)
        price_change_pct = round((price_change / previous_close) * 100, 2)

    # Format market cap
    market_cap_str = _format_market_cap(market_cap)

    return {
        "ticker":          ticker,
        "company_name":    company_name,
        "currency":        currency,
        "exchange":        exchange,
        "current_price":   current_price,
        "price_change":    price_change,
        "price_change_pct": price_change_pct,
        "open":            open_price,
        "day_high":        day_high,
        "day_low":         day_low,
        "previous_close":  previous_close,
        "volume":          volume,
        "market_cap":      market_cap,
        "market_cap_formatted": market_cap_str,
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status":          "success"
    }


def _format_market_cap(market_cap: int | None) -> str:
    """Convert raw market cap number to Indian format (Cr / Lakh Cr)."""
    if not market_cap:
        return "N/A"
    crore = market_cap / 1e7
    if crore >= 1_00_000:
        return f"₹{crore / 1_00_000:.2f} Lakh Cr"
    elif crore >= 1_000:
        return f"₹{crore:.0f} Cr"
    else:
        return f"₹{crore:.1f} Cr"
