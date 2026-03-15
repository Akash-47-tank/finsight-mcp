"""
FinSight MCP Server
===================
A production-style MCP server exposing Indian stock market tools,
resources, and prompt templates to any MCP-compatible client.

MCP Primitives demonstrated:
  - Tools    : get_stock_price, search_news, analyse_fundamentals, compare_stocks
  - Resources: nse_symbols.json, market_glossary.md, portfolio_template.txt
  - Prompts  : stock_analysis_prompt, portfolio_review_prompt
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from tools.stock_price import get_stock_price
from tools.news_search import search_news
from tools.fundamentals import analyse_fundamentals
from tools.compare_stocks import compare_stocks

# ── Server instance ──────────────────────────────────────────────────────────
app = Server("finsight-mcp")

RESOURCES_DIR = Path(__file__).parent / "resources"
PROMPTS_DIR   = Path(__file__).parent.parent / "prompts"


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TOOLS                                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_stock_price",
            description=(
                "Fetch the current live price and basic quote data for an Indian stock. "
                "Use NSE ticker format, e.g. 'TCS.NS', 'RELIANCE.NS', 'INFY.NS'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "NSE ticker symbol e.g. TCS.NS, RELIANCE.NS"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="search_news",
            description=(
                "Search for the latest financial news articles about a company or topic. "
                "Returns up to 5 recent headlines with summaries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query e.g. 'Reliance Industries earnings', 'HDFC Bank merger'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of articles to return (1-5, default 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="analyse_fundamentals",
            description=(
                "Get fundamental financial metrics for an Indian stock: "
                "P/E ratio, EPS, market cap, 52-week range, dividend yield, revenue, and more."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "NSE ticker symbol e.g. HDFCBANK.NS"
                    }
                },
                "required": ["ticker"]
            }
        ),
        types.Tool(
            name="compare_stocks",
            description=(
                "Compare multiple Indian stocks side-by-side on key metrics: "
                "price, market cap, P/E, 52-week performance, and sector."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of NSE tickers e.g. ['TCS.NS', 'INFY.NS', 'WIPRO.NS']",
                        "minItems": 2,
                        "maxItems": 5
                    }
                },
                "required": ["tickers"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        if name == "get_stock_price":
            result = get_stock_price(arguments["ticker"])
        elif name == "search_news":
            result = search_news(
                arguments["query"],
                arguments.get("max_results", 5)
            )
        elif name == "analyse_fundamentals":
            result = analyse_fundamentals(arguments["ticker"])
        elif name == "compare_stocks":
            result = compare_stocks(arguments["tickers"])
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        error_msg = {"error": str(e), "tool": name, "arguments": arguments}
        return [types.TextContent(type="text", text=json.dumps(error_msg, indent=2))]


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  RESOURCES                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="file://nse_symbols",
            name="NSE Stock Symbols",
            description="Top 50 NSE-listed company tickers with company names and sectors",
            mimeType="application/json"
        ),
        types.Resource(
            uri="file://market_glossary",
            name="Financial Market Glossary",
            description="Definitions of key financial terms used in stock analysis",
            mimeType="text/markdown"
        ),
        types.Resource(
            uri="file://portfolio_template",
            name="User Portfolio",
            description="The user's sample stock portfolio for review and analysis",
            mimeType="text/plain"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    resource_map = {
        "file://nse_symbols":       RESOURCES_DIR / "nse_symbols.json",
        "file://market_glossary":   RESOURCES_DIR / "market_glossary.md",
        "file://portfolio_template": RESOURCES_DIR / "portfolio_template.txt"
    }
    path = resource_map.get(uri)
    if not path or not path.exists():
        raise FileNotFoundError(f"Resource not found: {uri}")
    return path.read_text(encoding="utf-8")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PROMPTS                                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    return [
        types.Prompt(
            name="stock_analysis_prompt",
            description="Generate a structured deep-dive analysis report for a single stock",
            arguments=[
                types.PromptArgument(
                    name="ticker",
                    description="NSE ticker symbol e.g. RELIANCE.NS",
                    required=True
                ),
                types.PromptArgument(
                    name="timeframe",
                    description="Analysis timeframe e.g. 'short-term', 'long-term', '1 year'",
                    required=False
                )
            ]
        ),
        types.Prompt(
            name="portfolio_review_prompt",
            description="Review and score a user's stock portfolio with buy/hold/sell recommendations",
            arguments=[
                types.PromptArgument(
                    name="risk_profile",
                    description="Investor risk tolerance: 'conservative', 'moderate', or 'aggressive'",
                    required=True
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
    args = arguments or {}

    if name == "stock_analysis_prompt":
        ticker    = args.get("ticker", "TICKER.NS")
        timeframe = args.get("timeframe", "medium-term")
        template_path = PROMPTS_DIR / "stock_analysis.txt"
        template  = template_path.read_text(encoding="utf-8")
        content   = template.replace("{{ticker}}", ticker).replace("{{timeframe}}", timeframe)
        return types.GetPromptResult(
            description=f"Deep-dive analysis prompt for {ticker}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=content)
                )
            ]
        )

    elif name == "portfolio_review_prompt":
        risk_profile = args.get("risk_profile", "moderate")
        template_path = PROMPTS_DIR / "portfolio_review.txt"
        template  = template_path.read_text(encoding="utf-8")
        content   = template.replace("{{risk_profile}}", risk_profile)
        return types.GetPromptResult(
            description=f"Portfolio review prompt for {risk_profile} investor",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=content)
                )
            ]
        )

    raise ValueError(f"Unknown prompt: {name}")


# ── Entry point ──────────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
