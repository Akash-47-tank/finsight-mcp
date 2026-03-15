"""
Tool: compare_stocks
Compare 2-5 Indian stocks side-by-side on key financial metrics.
Uses yfinance — completely free, no API key needed.
"""

from typing import Any
import yfinance as yf
from datetime import datetime


def compare_stocks(tickers: list[str]) -> dict[str, Any]:
    """
    Compare multiple NSE-listed stocks on key metrics.

    Args:
        tickers: List of 2-5 NSE ticker symbols

    Returns:
        dict with a comparison table and a summary ranking
    """
    # Normalise tickers
    normalised = []
    for t in tickers:
        t = t.strip().upper()
        if "." not in t:
            t += ".NS"
        normalised.append(t)

    rows   = []
    errors = []

    for ticker in normalised:
        try:
            stock = yf.Ticker(ticker)
            info  = stock.info

            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            prev_close    = info.get("previousClose") or info.get("regularMarketPreviousClose")
            week_52_high  = info.get("fiftyTwoWeekHigh")
            week_52_low   = info.get("fiftyTwoWeekLow")
            market_cap    = info.get("marketCap")

            # 1-day change %
            day_change_pct = None
            if current_price and prev_close:
                day_change_pct = round(((current_price - prev_close) / prev_close) * 100, 2)

            # 52-week performance (position in range)
            week_52_pos = None
            if current_price and week_52_low and week_52_high and (week_52_high - week_52_low) > 0:
                week_52_pos = round(
                    ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100, 1
                )

            rows.append({
                "ticker":             ticker,
                "company":            info.get("longName") or info.get("shortName") or ticker,
                "sector":             info.get("sector", "N/A"),
                "current_price":      current_price,
                "day_change_pct":     day_change_pct,
                "pe_ratio":           _safe_round(info.get("trailingPE")),
                "pb_ratio":           _safe_round(info.get("priceToBook")),
                "eps":                _safe_round(info.get("trailingEps")),
                "market_cap":         _fmt_crore(market_cap),
                "52w_high":           week_52_high,
                "52w_low":            week_52_low,
                "52w_position_pct":   week_52_pos,
                "dividend_yield":     _fmt_pct(info.get("dividendYield")),
                "roe_pct":            _fmt_pct(info.get("returnOnEquity")),
                "profit_margin_pct":  _fmt_pct(info.get("profitMargins")),
                "debt_to_equity":     _safe_round(info.get("debtToEquity")),
                "revenue_growth_pct": _fmt_pct(info.get("revenueGrowth")),
            })
        except Exception as e:
            errors.append({"ticker": ticker, "error": str(e)})

    # ── Quick ranking summary ─────────────────────────────────────────────────
    summary = _build_summary(rows)

    return {
        "tickers_compared": normalised,
        "comparison_table": rows,
        "summary":          summary,
        "errors":           errors,
        "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status":           "success" if rows else "error"
    }


def _build_summary(rows: list[dict]) -> dict:
    """Generate simple best/worst rankings from the comparison table."""
    if len(rows) < 2:
        return {}

    valid = lambda key: [r for r in rows if isinstance(r.get(key), (int, float))]

    def best_by(key, lower_is_better=False):
        v = valid(key)
        if not v:
            return "N/A"
        pick = min(v, key=lambda r: r[key]) if lower_is_better else max(v, key=lambda r: r[key])
        return pick["ticker"]

    return {
        "best_day_performance":  best_by("day_change_pct"),
        "52w_strongest":         best_by("52w_position_pct"),
        "lowest_pe_ratio":       best_by("pe_ratio", lower_is_better=True),
        "highest_roe":           best_by("roe_pct"),          # already % string, skip
        "best_profit_margin":    best_by("profit_margin_pct"),
        "note": "Rankings based on available data; always do your own due diligence."
    }


def _safe_round(v, n=2):
    if v is None:
        return "N/A"
    try:
        return round(float(v), n)
    except Exception:
        return "N/A"


def _fmt_pct(v) -> str:
    if v is None:
        return "N/A"
    try:
        return f"{round(float(v) * 100, 2)}%"
    except Exception:
        return "N/A"


def _fmt_crore(v) -> str:
    if v is None:
        return "N/A"
    crore = float(v) / 1e7
    if abs(crore) >= 1_00_000:
        return f"₹{crore / 1_00_000:.2f} Lakh Cr"
    return f"₹{crore:,.0f} Cr"
