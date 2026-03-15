"""
FinSight MCP Client
===================
A custom MCP client that:
  1. Connects to the FinSight MCP server via stdio transport
  2. Discovers all tools, resources, and prompts from the server
  3. Runs a conversational chat loop powered by Ollama (local, free LLM)
  4. Decides which tool to call based on the user's message
  5. Injects resource context (portfolio, glossary) into the LLM prompt
  6. Uses server-defined prompt templates for structured analysis

Requirements:
  - Ollama running locally: https://ollama.com  (brew install ollama)
  - Pull a model: ollama pull llama3.2 (or mistral, gemma3)
  - pip install mcp httpx rich python-dotenv

Usage:
  python client/finsight_client.py
"""

import asyncio
import json
import os
import sys
import re
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

# Load environment variables from .env file
load_dotenv()

console = Console()

# ── Configuration ─────────────────────────────────────────────────────────────
SERVER_SCRIPT = Path(__file__).parent.parent / "server" / "finsight_server.py"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

SYSTEM_PROMPT = """You are FinSight, an expert Indian stock market analyst and financial advisor.
You have access to real-time tools for fetching NSE stock data, financial news, and fundamental analysis.

IMPORTANT INSTRUCTIONS:
1. When the user asks about a stock's price, ALWAYS call get_stock_price tool first.
2. When asked for analysis, call analyse_fundamentals AND search_news.
3. When comparing stocks, use compare_stocks tool.
4. Always use NSE ticker format with .NS suffix (e.g., TCS.NS, RELIANCE.NS, INFY.NS).
5. Be concise but informative. Format numbers in Indian style (₹, Cr, Lakh).
6. Add appropriate caveats — this is for educational purposes, not financial advice.

TOOLS — use EXACTLY these argument names (copy them precisely):

TOOL: get_stock_price
  Argument name: "ticker"  (string)
  Example: {"tool_call": {"name": "get_stock_price", "arguments": {"ticker": "TCS.NS"}}}

TOOL: search_news
  Argument name: "query"  (string), "max_results" (integer, optional)
  Example: {"tool_call": {"name": "search_news", "arguments": {"query": "Reliance Industries earnings", "max_results": 3}}}

TOOL: analyse_fundamentals
  Argument name: "ticker"  (string)
  Example: {"tool_call": {"name": "analyse_fundamentals", "arguments": {"ticker": "HDFCBANK.NS"}}}

TOOL: compare_stocks
  Argument name: "tickers"  (array of strings)
  Example: {"tool_call": {"name": "compare_stocks", "arguments": {"tickers": ["TCS.NS", "INFY.NS", "WIPRO.NS"]}}}

CRITICAL RULES:
- Use ONLY the argument names shown above. Never use "param", "symbol", "stock", or any other name.
- For get_stock_price and analyse_fundamentals: the key is "ticker" (singular).
- For compare_stocks: the key is "tickers" (plural) and the value is a JSON array [...].
- When you want to call a tool, respond ONLY with the JSON — no other text.
- After receiving tool results, summarise them clearly in plain English.
"""


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  OLLAMA INTEGRATION                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════╝

async def call_ollama(messages: list[dict], model: str = OLLAMA_MODEL) -> str:
    """Send messages to local Ollama and return the assistant's response."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,   # Lower temp for more factual responses
                        "num_ctx":     4096
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.ConnectError:
            return (
                "[ERROR] Cannot connect to Ollama. "
                "Make sure Ollama is running: `ollama serve` in a separate terminal."
            )
        except Exception as e:
            return f"[ERROR] Ollama error: {str(e)}"


async def check_ollama_available() -> tuple[bool, list[str]]:
    """Check if Ollama is running and return available models."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return True, models
        except Exception:
            return False, []


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  TOOL CALL PARSING                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def extract_tool_call(text: str) -> dict | None:
    """
    Parse a tool call JSON from the LLM's response.
    Handles both clean JSON and JSON embedded in text.
    Also fixes common LLM mistakes like using 'param' instead of the real arg name.
    """
    raw = text.strip()

    # Try direct parse first
    parsed = None
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
            if "tool_call" in data:
                parsed = data["tool_call"]
        except json.JSONDecodeError:
            pass

    # Try extracting JSON block embedded in prose
    if not parsed:
        json_match = re.search(r'\{[^{}]*"tool_call"\s*:\s*\{.*?\}\s*\}', raw, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if "tool_call" in data:
                    parsed = data["tool_call"]
            except json.JSONDecodeError:
                pass

    if not parsed:
        return None

    # ── Auto-fix wrong argument names the LLM commonly uses ──────────────────
    name = parsed.get("name", "")
    args = parsed.get("arguments", {})

    # Rename any wrong key → correct key for each tool
    wrong_single_keys  = {"param", "symbol", "stock", "ticker_symbol", "stock_ticker",
                          "stockticker", "stock_symbol", "code", "nse_ticker"}
    wrong_plural_keys  = {"param", "symbols", "stocks", "ticker_list", "stock_list",
                          "tickers_list", "list"}

    if name in ("get_stock_price", "analyse_fundamentals"):
        # Correct arg name is "ticker"
        for wrong in wrong_single_keys:
            if wrong in args and "ticker" not in args:
                args["ticker"] = args.pop(wrong)
                break

    elif name == "compare_stocks":
        # Correct arg name is "tickers" (list)
        for wrong in wrong_plural_keys:
            if wrong in args and "tickers" not in args:
                val = args.pop(wrong)
                # If LLM passed a string instead of list, parse it
                if isinstance(val, str):
                    val = [v.strip().strip("'\"") for v in val.strip("[]").split(",") if v.strip()]
                args["tickers"] = val
                break
        # Ensure tickers is always a list, not a string
        if "tickers" in args and isinstance(args["tickers"], str):
            args["tickers"] = [v.strip().strip("'\"") for v in args["tickers"].strip("[]").split(",") if v.strip()]

    elif name == "search_news":
        # Correct arg name is "query"
        for wrong in {"param", "search", "search_query", "term", "keywords", "q"}:
            if wrong in args and "query" not in args:
                args["query"] = args.pop(wrong)
                break

    parsed["arguments"] = args
    return parsed


def detect_tool_from_user_input(user_input: str) -> dict | None:
    """
    Keyword-based direct tool routing — bypasses LLM argument guessing
    for simple, clearly-phrased queries. Acts as a fast-path before
    sending to the LLM.

    Returns a tool_call dict if confident, or None to fall through to LLM.
    """
    text = user_input.lower().strip()

    # Known NSE tickers to extract from user input
    nse_map = {
        "tcs": "TCS.NS", "reliance": "RELIANCE.NS", "infy": "INFY.NS",
        "infosys": "INFY.NS", "wipro": "WIPRO.NS", "hdfc bank": "HDFCBANK.NS",
        "hdfcbank": "HDFCBANK.NS", "hdfc": "HDFCBANK.NS", "icici": "ICICIBANK.NS",
        "icici bank": "ICICIBANK.NS", "sbi": "SBIN.NS", "itc": "ITC.NS",
        "kotak": "KOTAKBANK.NS", "axis bank": "AXISBANK.NS", "axis": "AXISBANK.NS",
        "bajaj finance": "BAJFINANCE.NS", "sun pharma": "SUNPHARMA.NS",
        "sunpharma": "SUNPHARMA.NS", "maruti": "MARUTI.NS", "tata motors": "TATAMOTORS.NS",
        "tatamotors": "TATAMOTORS.NS", "adani": "ADANIENT.NS", "hcl": "HCLTECH.NS",
        "tech mahindra": "TECHM.NS", "techm": "TECHM.NS", "titan": "TITAN.NS",
        "ongc": "ONGC.NS", "ntpc": "NTPC.NS", "powergrid": "POWERGRID.NS",
        "britannia": "BRITANNIA.NS", "asian paints": "ASIANPAINT.NS",
        "nestle": "NESTLEIND.NS", "dr reddy": "DRREDDY.NS", "cipla": "CIPLA.NS",
    }

    # Extract any explicit .NS ticker from text (e.g. "TCS.NS")
    ns_match = re.search(r'\b([A-Z&-]{2,15}\.NS)\b', user_input.upper())
    explicit_ticker = ns_match.group(1) if ns_match else None

    # Price queries: "price of X", "how much is X", "what is X trading at"
    price_triggers = ["price of", "price for", "current price", "stock price",
                      "trading at", "how much is", "what is the price", "share price",
                      "quote for", "quote of", "rate of"]
    if any(t in text for t in price_triggers):
        ticker = explicit_ticker
        if not ticker:
            for name, sym in nse_map.items():
                if name in text:
                    ticker = sym
                    break
        if ticker:
            return {"name": "get_stock_price", "arguments": {"ticker": ticker}}

    # Compare queries: "compare X and Y", "X vs Y", "difference between X and Y"
    compare_triggers = ["compare", " vs ", " versus ", "difference between", "which is better"]
    if any(t in text for t in compare_triggers):
        found = []
        for name, sym in nse_map.items():
            if name in text and sym not in found:
                found.append(sym)
        # Also catch explicit .NS tickers
        for m in re.finditer(r'\b([A-Z&-]{2,15}\.NS)\b', user_input.upper()):
            sym = m.group(1)
            if sym not in found:
                found.append(sym)
        if len(found) >= 2:
            return {"name": "compare_stocks", "arguments": {"tickers": found}}

    # News queries: "news about X", "latest news on X"
    news_triggers = ["news about", "news on", "latest news", "recent news",
                     "headlines", "what happened with", "updates on"]
    if any(t in text for t in news_triggers):
        query = user_input  # pass the full query for best results
        return {"name": "search_news", "arguments": {"query": query, "max_results": 5}}

    return None  # Fall through to LLM


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  DISPLAY HELPERS                                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def display_welcome():
    console.print(Panel.fit(
        "[bold green]FinSight MCP[/bold green] — Indian Stock Market Research Assistant\n"
        "[dim]Powered by: MCP Server + Ollama (local LLM) + yfinance[/dim]\n\n"
        "Commands:\n"
        "  [cyan]Type any question[/cyan] about Indian stocks\n"
        "  [cyan]resources[/cyan] — list available resources\n"
        "  [cyan]tools[/cyan]     — list available tools\n"
        "  [cyan]prompts[/cyan]   — list prompt templates\n"
        "  [cyan]analyse <TICKER>[/cyan] — deep analysis using prompt template\n"
        "  [cyan]portfolio[/cyan] — review your portfolio\n"
        "  [cyan]quit[/cyan]      — exit",
        title="[bold]Welcome to FinSight[/bold]",
        border_style="green"
    ))


def display_tool_result(tool_name: str, result: Any):
    """Pretty-print tool results in the terminal."""
    try:
        data = json.loads(result) if isinstance(result, str) else result
        console.print(Panel(
            f"[dim]{json.dumps(data, indent=2, ensure_ascii=False)[:2000]}[/dim]",
            title=f"[yellow]Tool Result: {tool_name}[/yellow]",
            border_style="yellow"
        ))
    except Exception:
        console.print(f"[yellow]Tool result:[/yellow] {result}")


def display_server_capabilities(tools, resources, prompts):
    """Display what the MCP server exposes."""
    # Tools table
    t = Table(title="Available MCP Tools", border_style="cyan")
    t.add_column("Tool Name", style="cyan")
    t.add_column("Description")
    for tool in tools:
        t.add_row(tool.name, tool.description[:80] + "..." if len(tool.description) > 80 else tool.description)
    console.print(t)

    # Resources table
    r = Table(title="Available MCP Resources", border_style="blue")
    r.add_column("URI", style="blue")
    r.add_column("Name")
    r.add_column("Description")
    for res in resources:
        r.add_row(str(res.uri), res.name, (res.description or "")[:60])
    console.print(r)

    # Prompts table
    p = Table(title="Available MCP Prompts", border_style="magenta")
    p.add_column("Prompt Name", style="magenta")
    p.add_column("Description")
    for prompt in prompts:
        p.add_row(prompt.name, prompt.description or "")
    console.print(p)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MAIN CLIENT LOOP                                                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝

async def run_client():
    display_welcome()

    # ── Check Ollama ──────────────────────────────────────────────────────────
    console.print("[dim]Checking Ollama availability...[/dim]")
    ollama_ok, available_models = await check_ollama_available()

    if not ollama_ok:
        console.print(
            "[red]⚠ Ollama not running.[/red] "
            "Start it with: [cyan]ollama serve[/cyan]\n"
            "Install: [cyan]brew install ollama[/cyan] then [cyan]ollama pull llama3.2[/cyan]"
        )
        console.print("[yellow]Continuing in tool-only mode (no LLM responses)...[/yellow]")
    else:
        model_display = OLLAMA_MODEL
        if available_models and OLLAMA_MODEL not in " ".join(available_models):
            # Suggest first available model
            model_display = available_models[0] if available_models else OLLAMA_MODEL
            console.print(f"[yellow]Model '{OLLAMA_MODEL}' not found. Using '{model_display}'[/yellow]")
            console.print(f"[dim]To pull the default: ollama pull {OLLAMA_MODEL}[/dim]")
        console.print(f"[green]✓ Ollama connected — model: {model_display}[/green]")

    # ── Connect to MCP Server ─────────────────────────────────────────────────
    console.print("[dim]Connecting to FinSight MCP server...[/dim]")

    server_params = StdioServerParameters(
        command="python",
        args=[str(SERVER_SCRIPT)],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # Initialise the MCP session
            await session.initialize()
            console.print("[green]✓ MCP server connected and initialised[/green]\n")

            # ── Discover server capabilities ──────────────────────────────────
            tools_result     = await session.list_tools()
            resources_result = await session.list_resources()
            prompts_result   = await session.list_prompts()

            tools     = tools_result.tools
            resources = resources_result.resources
            prompts   = prompts_result.prompts

            tool_names   = [t.name for t in tools]
            prompt_names = [p.name for p in prompts]

            console.print(
                f"[green]Server exposes: "
                f"{len(tools)} tools · "
                f"{len(resources)} resources · "
                f"{len(prompts)} prompts[/green]\n"
            )

            # ── Load portfolio resource into context ──────────────────────────
            portfolio_context = ""
            try:
                portfolio_res = await session.read_resource("file://portfolio_template")
                for content in portfolio_res.contents:
                    portfolio_context = content.text
            except Exception:
                pass  # Resource load failure is non-fatal

            # ── Conversation history for multi-turn context ───────────────────
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            if portfolio_context:
                messages.append({
                    "role": "system",
                    "content": f"USER'S PORTFOLIO (from MCP resource):\n{portfolio_context}"
                })

            # ═══════════════════════════════════════════════════════════════════
            #  MAIN CHAT LOOP
            # ═══════════════════════════════════════════════════════════════════
            while True:
                try:
                    user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                except (KeyboardInterrupt, EOFError):
                    console.print("\n[dim]Goodbye![/dim]")
                    break

                if not user_input:
                    continue

                cmd = user_input.lower()

                # ── Built-in commands ─────────────────────────────────────────
                if cmd in ("quit", "exit", "q"):
                    console.print("[dim]Goodbye![/dim]")
                    break

                elif cmd == "tools":
                    display_server_capabilities(tools, resources, prompts)
                    continue

                elif cmd == "resources":
                    for res in resources:
                        console.print(f"[blue]{res.uri}[/blue] — {res.name}")
                    continue

                elif cmd == "prompts":
                    for p in prompts:
                        console.print(f"[magenta]{p.name}[/magenta] — {p.description}")
                    continue

                # ── analyse <TICKER> — use stock_analysis_prompt template ─────
                elif cmd.startswith("analyse "):
                    ticker = cmd.replace("analyse ", "").strip().upper()
                    if "." not in ticker:
                        ticker += ".NS"
                    try:
                        console.print(f"[dim]Loading stock_analysis_prompt for {ticker}...[/dim]")
                        prompt_result = await session.get_prompt(
                            "stock_analysis_prompt",
                            {"ticker": ticker, "timeframe": "medium-term"}
                        )
                        prompt_text = prompt_result.messages[0].content.text
                        messages.append({"role": "user", "content": prompt_text})

                        # Gather fundamentals and news automatically
                        console.print(f"[dim]Fetching fundamentals for {ticker}...[/dim]")
                        fund_result = await session.call_tool("analyse_fundamentals", {"ticker": ticker})
                        fund_text   = fund_result.content[0].text

                        console.print(f"[dim]Fetching news for {ticker}...[/dim]")
                        news_result = await session.call_tool("search_news", {"query": ticker.replace(".NS", "")})
                        news_text   = news_result.content[0].text

                        context_msg = (
                            f"FUNDAMENTALS DATA:\n{fund_text}\n\n"
                            f"RECENT NEWS:\n{news_text}"
                        )
                        messages.append({"role": "user", "content": context_msg})

                        console.print("[dim]Generating analysis report...[/dim]")
                        response = await call_ollama(messages)
                        messages.append({"role": "assistant", "content": response})
                        console.print(Panel(Markdown(response), title=f"[green]FinSight Analysis: {ticker}[/green]", border_style="green"))
                    except Exception as e:
                        console.print(f"[red]Error in analysis: {e}[/red]")
                    continue

                # ── portfolio — use portfolio_review_prompt template ───────────
                elif cmd == "portfolio":
                    try:
                        console.print("[dim]Loading portfolio_review_prompt...[/dim]")
                        prompt_result = await session.get_prompt(
                            "portfolio_review_prompt",
                            {"risk_profile": "moderate"}
                        )
                        prompt_text = prompt_result.messages[0].content.text
                        messages.append({"role": "user", "content": prompt_text})

                        console.print("[dim]Generating portfolio review...[/dim]")
                        response = await call_ollama(messages)
                        messages.append({"role": "assistant", "content": response})
                        console.print(Panel(Markdown(response), title="[green]Portfolio Review[/green]", border_style="green"))
                    except Exception as e:
                        console.print(f"[red]Error in portfolio review: {e}[/red]")
                    continue

                # ── Regular conversational query ──────────────────────────────
                messages.append({"role": "user", "content": user_input})

                # FAST PATH: keyword-based direct tool routing (no LLM needed)
                direct_tool_call = detect_tool_from_user_input(user_input)

                if direct_tool_call and direct_tool_call.get("name") in tool_names:
                    tool_name = direct_tool_call["name"]
                    tool_args = direct_tool_call.get("arguments", {})
                    console.print(f"[dim]Calling tool: [yellow]{tool_name}[/yellow] with {tool_args}...[/dim]")
                    try:
                        tool_result = await session.call_tool(tool_name, tool_args)
                        result_text = tool_result.content[0].text
                        display_tool_result(tool_name, result_text)
                        messages.append({"role": "assistant", "content": f"[called {tool_name}]"})
                        messages.append({
                            "role": "user",
                            "content": f"Tool '{tool_name}' returned this data:\n{result_text}\n\nPlease summarise this clearly for the user."
                        })
                        final_response = await call_ollama(messages)
                        messages.append({"role": "assistant", "content": final_response})
                        console.print(Panel(Markdown(final_response), title="[green]FinSight[/green]", border_style="green"))
                    except Exception as e:
                        console.print(f"[red]Tool call failed: {e}[/red]")

                else:
                    # SLOW PATH: ask LLM to decide what to do
                    console.print("[dim]Thinking...[/dim]")
                    llm_response = await call_ollama(messages)

                    # Try to parse a tool call from LLM response
                    tool_call = extract_tool_call(llm_response)

                    if tool_call and tool_call.get("name") in tool_names:
                        tool_name = tool_call["name"]
                        tool_args = tool_call.get("arguments", {})
                        console.print(f"[dim]Calling tool: [yellow]{tool_name}[/yellow] with {tool_args}...[/dim]")
                        try:
                            tool_result = await session.call_tool(tool_name, tool_args)
                            result_text = tool_result.content[0].text
                            display_tool_result(tool_name, result_text)
                            messages.append({"role": "assistant", "content": llm_response})
                            messages.append({
                                "role": "user",
                                "content": f"Tool '{tool_name}' returned this data:\n{result_text}\n\nPlease summarise this clearly for the user."
                            })
                            final_response = await call_ollama(messages)
                            messages.append({"role": "assistant", "content": final_response})
                            console.print(Panel(Markdown(final_response), title="[green]FinSight[/green]", border_style="green"))
                        except Exception as e:
                            console.print(f"[red]Tool call failed: {e}[/red]")
                    else:
                        # Pure LLM answer — no tool needed
                        messages.append({"role": "assistant", "content": llm_response})
                        console.print(Panel(Markdown(llm_response), title="[green]FinSight[/green]", border_style="green"))

                # Keep context window manageable (last 20 messages)
                if len(messages) > 22:
                    messages = messages[:2] + messages[-20:]   # keep system prompts + last 20



async def main():
    await run_client()


if __name__ == "__main__":
    asyncio.run(main())