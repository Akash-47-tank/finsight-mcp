"""
Tool: analyse_fundamentals
Returns detailed fundamental financial metrics for an NSE-listed stock.
Uses yfinance — completely free, no API key needed.
"""

from typing import Any
import yfinance as yf
from datetime import datetime


def analyse_fundamentals(ticker: str) -> dict[str, Any]:
    """
    Fetch comprehensive fundamental data for a stock.

    Args:
        ticker: NSE ticker e.g. 'HDFCBANK.NS'

    Returns:
        dict with valuation, profitability, growth, and balance sheet metrics
    """
    if "." not in ticker:
        ticker = ticker.upper() + ".NS"
    else:
        ticker = ticker.upper()

    stock = yf.Ticker(ticker)
    info  = stock.info

    # ── Valuation Metrics ────────────────────────────────────────────────────
    pe_ratio          = info.get("trailingPE")
    forward_pe        = info.get("forwardPE")
    pb_ratio          = info.get("priceToBook")
    ps_ratio          = info.get("priceToSalesTrailing12Months")
    peg_ratio         = info.get("pegRatio")
    ev_ebitda         = info.get("enterpriseToEbitda")
    market_cap        = info.get("marketCap")

    # ── Profitability ────────────────────────────────────────────────────────
    eps_ttm           = info.get("trailingEps")
    eps_forward       = info.get("forwardEps")
    roe               = info.get("returnOnEquity")
    roa               = info.get("returnOnAssets")
    profit_margins    = info.get("profitMargins")
    operating_margins = info.get("operatingMargins")
    gross_margins     = info.get("grossMargins")

    # ── Revenue & Growth ────────────────────────────────────────────────────
    revenue           = info.get("totalRevenue")
    revenue_growth    = info.get("revenueGrowth")
    earnings_growth   = info.get("earningsGrowth")
    ebitda            = info.get("ebitda")
    free_cashflow     = info.get("freeCashflow")

    # ── Price & Range ────────────────────────────────────────────────────────
    current_price     = info.get("currentPrice") or info.get("regularMarketPrice")
    week_52_high      = info.get("fiftyTwoWeekHigh")
    week_52_low       = info.get("fiftyTwoWeekLow")
    fifty_day_avg     = info.get("fiftyDayAverage")
    two_hundred_day_avg = info.get("twoHundredDayAverage")

    # ── Dividend ─────────────────────────────────────────────────────────────
    dividend_yield    = info.get("dividendYield")
    dividend_rate     = info.get("dividendRate")
    payout_ratio      = info.get("payoutRatio")

    # ── Balance Sheet ────────────────────────────────────────────────────────
    total_debt        = info.get("totalDebt")
    total_cash        = info.get("totalCash")
    debt_to_equity    = info.get("debtToEquity")
    current_ratio     = info.get("currentRatio")
    book_value        = info.get("bookValue")

    # ── 52-week performance ──────────────────────────────────────────────────
    week_52_perf = None
    if current_price and week_52_low and week_52_high:
        week_52_perf = round(
            ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100, 1
        ) if (week_52_high - week_52_low) > 0 else 0

    # ── Distance from 52W high ───────────────────────────────────────────────
    from_52w_high = None
    if current_price and week_52_high:
        from_52w_high = round(((current_price - week_52_high) / week_52_high) * 100, 2)

    return {
        "ticker":       ticker,
        "company_name": info.get("longName") or info.get("shortName") or ticker,
        "sector":       info.get("sector", "N/A"),
        "industry":     info.get("industry", "N/A"),
        "currency":     info.get("currency", "INR"),
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "valuation": {
            "market_cap_formatted": _fmt_crore(market_cap),
            "market_cap_raw":       market_cap,
            "pe_ratio_ttm":         _fmt_float(pe_ratio),
            "forward_pe":           _fmt_float(forward_pe),
            "pb_ratio":             _fmt_float(pb_ratio),
            "ps_ratio_ttm":         _fmt_float(ps_ratio),
            "peg_ratio":            _fmt_float(peg_ratio),
            "ev_to_ebitda":         _fmt_float(ev_ebitda)
        },

        "profitability": {
            "eps_ttm":              _fmt_float(eps_ttm),
            "eps_forward":          _fmt_float(eps_forward),
            "roe_pct":              _fmt_pct(roe),
            "roa_pct":              _fmt_pct(roa),
            "profit_margin_pct":    _fmt_pct(profit_margins),
            "operating_margin_pct": _fmt_pct(operating_margins),
            "gross_margin_pct":     _fmt_pct(gross_margins)
        },

        "revenue_and_growth": {
            "total_revenue_formatted": _fmt_crore(revenue),
            "revenue_growth_pct":      _fmt_pct(revenue_growth),
            "earnings_growth_pct":     _fmt_pct(earnings_growth),
            "ebitda_formatted":        _fmt_crore(ebitda),
            "free_cashflow_formatted": _fmt_crore(free_cashflow)
        },

        "price_data": {
            "current_price":        current_price,
            "52w_high":             week_52_high,
            "52w_low":              week_52_low,
            "52w_position_pct":     week_52_perf,
            "from_52w_high_pct":    from_52w_high,
            "50_day_avg":           _fmt_float(fifty_day_avg),
            "200_day_avg":          _fmt_float(two_hundred_day_avg)
        },

        "dividends": {
            "dividend_yield_pct":   _fmt_pct(dividend_yield),
            "annual_dividend_rate": _fmt_float(dividend_rate),
            "payout_ratio_pct":     _fmt_pct(payout_ratio)
        },

        "balance_sheet": {
            "total_debt_formatted":  _fmt_crore(total_debt),
            "total_cash_formatted":  _fmt_crore(total_cash),
            "debt_to_equity":        _fmt_float(debt_to_equity),
            "current_ratio":         _fmt_float(current_ratio),
            "book_value_per_share":  _fmt_float(book_value)
        },

        "status": "success"
    }


def _fmt_float(v) -> str:
    if v is None:
        return "N/A"
    return round(float(v), 2)


def _fmt_pct(v) -> str:
    if v is None:
        return "N/A"
    return f"{round(float(v) * 100, 2)}%"


def _fmt_crore(v) -> str:
    if v is None:
        return "N/A"
    crore = float(v) / 1e7
    if abs(crore) >= 1_00_000:
        return f"₹{crore / 1_00_000:.2f} Lakh Cr"
    return f"₹{crore:,.0f} Cr"
