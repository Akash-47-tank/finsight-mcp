"""
FinSight MCP — Tool Tests
=========================
Run with: python -m pytest tests/test_tools.py -v
Or:        python tests/test_tools.py

Tests verify that each tool returns the expected data structure
without requiring a live MCP session.
"""

import sys
import json
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from tools.stock_price    import get_stock_price
from tools.fundamentals   import analyse_fundamentals
from tools.compare_stocks import compare_stocks
from tools.news_search    import search_news


# ── Helper ────────────────────────────────────────────────────────────────────
def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def passed(test: str):
    print(f"  ✓ {test}")


def failed(test: str, error: str):
    print(f"  ✗ {test}: {error}")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TEST: get_stock_price                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def test_get_stock_price():
    section("Testing: get_stock_price")

    # Test with .NS suffix
    result = get_stock_price("TCS.NS")
    assert result["status"] == "success",        "Status should be success"
    assert result["ticker"] == "TCS.NS",         "Ticker should match"
    assert "current_price" in result,            "Should have current_price"
    assert "company_name" in result,             "Should have company_name"
    assert "market_cap_formatted" in result,     "Should have formatted market cap"
    passed("TCS.NS — all required fields present")

    # Test without .NS suffix (should auto-add)
    result2 = get_stock_price("RELIANCE")
    assert result2["ticker"] == "RELIANCE.NS",   "Should auto-add .NS suffix"
    passed("RELIANCE (no suffix) — auto-corrected to RELIANCE.NS")

    # Test price change calculation
    if result["current_price"] and result["previous_close"]:
        assert result["price_change"] is not None,     "Should calculate price change"
        assert result["price_change_pct"] is not None, "Should calculate % change"
        passed("Price change calculation — working")

    print(f"\n  Sample output:")
    print(f"    Company: {result.get('company_name')}")
    print(f"    Price:   ₹{result.get('current_price')}")
    print(f"    Change:  {result.get('price_change_pct')}%")
    print(f"    Mkt Cap: {result.get('market_cap_formatted')}")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TEST: analyse_fundamentals                                              ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def test_analyse_fundamentals():
    section("Testing: analyse_fundamentals")

    result = analyse_fundamentals("HDFCBANK.NS")
    assert result["status"] == "success",        "Status should be success"
    assert "valuation" in result,                "Should have valuation section"
    assert "profitability" in result,            "Should have profitability section"
    assert "price_data" in result,               "Should have price_data section"
    assert "balance_sheet" in result,            "Should have balance_sheet section"
    assert "dividends" in result,                "Should have dividends section"
    passed("HDFCBANK.NS — all sections present")

    # Check valuation sub-keys
    val = result["valuation"]
    assert "pe_ratio_ttm" in val,               "Should have P/E ratio"
    assert "market_cap_formatted" in val,        "Should have formatted market cap"
    passed("Valuation section — all keys present")

    # Check profitability sub-keys
    prof = result["profitability"]
    assert "roe_pct" in prof,                    "Should have ROE"
    assert "profit_margin_pct" in prof,          "Should have profit margin"
    passed("Profitability section — all keys present")

    print(f"\n  Sample output:")
    print(f"    Company: {result.get('company_name')}")
    print(f"    Sector:  {result.get('sector')}")
    print(f"    P/E:     {result['valuation'].get('pe_ratio_ttm')}")
    print(f"    ROE:     {result['profitability'].get('roe_pct')}")
    print(f"    Mkt Cap: {result['valuation'].get('market_cap_formatted')}")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TEST: compare_stocks                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def test_compare_stocks():
    section("Testing: compare_stocks")

    tickers = ["TCS.NS", "INFY.NS", "WIPRO.NS"]
    result  = compare_stocks(tickers)

    assert result["status"] == "success",               "Status should be success"
    assert "comparison_table" in result,                "Should have comparison_table"
    assert "summary" in result,                         "Should have summary"
    assert len(result["comparison_table"]) == 3,        "Should have 3 rows"
    passed("3 stocks compared — table and summary present")

    # Check each row has required fields
    for row in result["comparison_table"]:
        assert "ticker" in row,       f"Row should have ticker: {row}"
        assert "current_price" in row, f"Row should have current_price: {row}"
        assert "pe_ratio" in row,      f"Row should have pe_ratio: {row}"
    passed("Each row has required fields")

    # Test auto-suffix addition
    result2 = compare_stocks(["TCS", "INFY"])
    assert any(r["ticker"] == "TCS.NS" for r in result2["comparison_table"]), "Should auto-add .NS"
    passed("Auto-adds .NS suffix when missing")

    print(f"\n  Sample comparison:")
    for row in result["comparison_table"]:
        print(f"    {row['ticker']:<18} ₹{row.get('current_price'):<10} P/E: {row.get('pe_ratio')}")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TEST: search_news                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def test_search_news():
    section("Testing: search_news")

    result = search_news("Reliance Industries", max_results=3)
    assert result["status"] == "success",   "Status should be success"
    assert "articles" in result,            "Should have articles list"
    assert "query" in result,               "Should have original query"
    assert "source" in result,              "Should have source info"
    passed("search_news — structure correct")

    # Check article structure
    if result["articles"]:
        article = result["articles"][0]
        assert "title" in article,        "Article should have title"
        assert "description" in article,  "Article should have description"
        passed("Article structure — all required fields present")

    print(f"\n  Source: {result.get('source')}")
    print(f"  Articles returned: {result.get('count')}")
    if result["articles"]:
        print(f"  First headline: {result['articles'][0].get('title', '')[:80]}...")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TEST: Resources                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝
def test_resources_exist():
    section("Testing: Resource files exist")

    resources_dir = Path(__file__).parent.parent / "server" / "resources"
    prompts_dir   = Path(__file__).parent.parent / "prompts"

    files_to_check = [
        resources_dir / "nse_symbols.json",
        resources_dir / "market_glossary.md",
        resources_dir / "portfolio_template.txt",
        prompts_dir   / "stock_analysis.txt",
        prompts_dir   / "portfolio_review.txt"
    ]

    for f in files_to_check:
        assert f.exists(), f"Missing file: {f}"
        passed(f.name)

    # Validate JSON structure of nse_symbols
    with open(resources_dir / "nse_symbols.json") as fp:
        data = json.load(fp)
    assert "symbols" in data,    "nse_symbols.json should have 'symbols' key"
    assert len(data["symbols"]) > 10, "Should have at least 10 symbols"
    passed(f"nse_symbols.json valid JSON with {len(data['symbols'])} symbols")

    # Check prompt templates have placeholders
    analysis_tmpl = (prompts_dir / "stock_analysis.txt").read_text()
    assert "{{ticker}}"    in analysis_tmpl, "stock_analysis.txt should have {{ticker}} placeholder"
    assert "{{timeframe}}" in analysis_tmpl, "stock_analysis.txt should have {{timeframe}} placeholder"
    passed("stock_analysis.txt has correct placeholders")

    portfolio_tmpl = (prompts_dir / "portfolio_review.txt").read_text()
    assert "{{risk_profile}}" in portfolio_tmpl, "portfolio_review.txt should have {{risk_profile}} placeholder"
    passed("portfolio_review.txt has correct placeholders")


# ── Run all tests ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  FinSight MCP — Test Suite")
    print("="*60)
    print("  Note: Tests make live API calls to Yahoo Finance.")
    print("  Ensure you have internet access.")

    all_passed = True

    test_functions = [
        ("Resource files",      test_resources_exist),
        ("get_stock_price",     test_get_stock_price),
        ("analyse_fundamentals",test_analyse_fundamentals),
        ("compare_stocks",      test_compare_stocks),
        ("search_news",         test_search_news),
    ]

    for name, fn in test_functions:
        try:
            fn()
        except AssertionError as e:
            print(f"\n  [FAIL] {name}: {e}")
            all_passed = False
        except Exception as e:
            print(f"\n  [ERROR] {name}: {type(e).__name__}: {e}")
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print("  ALL TESTS PASSED ✓")
    else:
        print("  SOME TESTS FAILED ✗ — check above for details")
    print("="*60 + "\n")
