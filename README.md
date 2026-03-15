# 📈 FinSight MCP — Agentic Indian Stock Market Research Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-FF6B35?style=for-the-badge)
![Ollama](https://img.shields.io/badge/LLM-Ollama%20Local-2ECC71?style=for-the-badge)
![yfinance](https://img.shields.io/badge/Data-yfinance%20Free-F39C12?style=for-the-badge)
![NSE](https://img.shields.io/badge/Market-NSE%20India-0066CC?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

**A production-style implementation of Anthropic's Model Context Protocol (MCP) that transforms a local LLM into an agentic financial research assistant for Indian NSE stocks — built 100% with free and open-source tools.**

*Completed after finishing the [Anthropic Academy — Introduction to Model Context Protocol](https://anthropic.com) course*

</div>

---

## 📌 Table of Contents

- [What is This Project?](#-what-is-this-project)
- [Live Demo Screenshots](#-live-demo-screenshots)
- [What is MCP? My Understanding](#-what-is-mcp-my-understanding)
- [Architecture and Flow Diagram](#-architecture-and-flow-diagram)
- [MCP Primitives Implemented](#-mcp-primitives-implemented)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack-100-free)
- [Setup and Installation](#-setup-and-installation-macos-m1)
- [How to Run](#-how-to-run)
- [Key Implementation Details](#-key-implementation-details)
- [Outcomes and Results](#-outcomes-and-results)
- [What I Learned](#-what-i-learned)
- [Possible Extensions](#-possible-extensions)

---

## 🎯 What is This Project?

FinSight MCP is a **complete, end-to-end implementation** of the Model Context Protocol. It consists of two parts working together:

1. **An MCP Server** (`finsight_server.py`) — exposes Indian stock market capabilities through all 3 MCP primitives: Tools, Resources, and Prompts
2. **A Custom MCP Client** (`finsight_client.py`) — connects to the server, discovers its capabilities, and runs a conversational chat loop powered by a local Ollama LLM

The core insight this project demonstrates: **MCP separates the "what the AI can do" (server) from "how the AI is used" (client)** — making AI capabilities modular, reusable, and composable across any client.

### Why Indian Stock Market?

I work as a Junior Data Scientist at a brokerage firm (Pure Broking Pvt. Ltd.) and have hands-on experience building RAG systems for regulatory compliance using Anthropic and OpenAI APIs. Combining MCP with the Indian financial market domain made this project authentic to my real-world work, immediately demonstrating practical value to recruiters in the fintech/AI space.

---

## 📸 Live Demo Screenshots

### 1. MCP Inspector — Server Connection

> The MCP Inspector is a developer tool that connects directly to an MCP server and lets you browse and test all exposed tools, resources, and prompts without needing a full client. Think of it as **Postman, but for MCP servers**.

![MCP Inspector](screenshots/inspector_disconnected.png)

*Inspector launched with Transport Type: STDIO, Command: python, Arguments: path to finsight_server.py. Clicking Connect spawns the server and discovers all capabilities.*

---

### 2. All MCP Primitives Visible in One Screen

> Typing `tools` in the chat client triggers calls to `list_tools()`, `list_resources()`, and `list_prompts()` on the server — demonstrating complete discovery of all three MCP primitives.

![Tools Resources Prompts](screenshots/tools_resources_prompts.png)

**What this demonstrates:**
- **4 MCP Tools** — callable functions: `get_stock_price`, `search_news`, `analyse_fundamentals`, `compare_stocks`
- **3 MCP Resources** — context files served at URIs: `file://nse_symbols`, `file://market_glossary`, `file://portfolio_template`
- **2 MCP Prompts** — server-side templates: `stock_analysis_prompt`, `portfolio_review_prompt`

This single screen proves all three MCP primitives are working correctly on the server.

---

### 3. Live Tool Execution — Real-Time Stock Price

> Asking "What is the current price of TCS?" triggers the keyword router, which directly calls `get_stock_price` with `{"ticker": "TCS.NS"}`. The raw JSON tool result is displayed before the LLM summarises it in natural language.

![TCS Live Price](screenshots/tcs_price.png)

**What this demonstrates:**
- MCP client successfully routes to `get_stock_price` tool with correct arguments
- Tool calls Yahoo Finance (yfinance) and returns structured JSON in real time
- **Live data: TCS at ₹2,410.50 (−1.31% on the day), Market Cap ₹8.72 Lakh Cr, Volume 24,66,012**
- The LLM then summarises the JSON into a clean, human-readable response
- Notice the timestamp `2026-03-15 14:49:46` — this is genuinely live data

---

### 4. Multi-Stock Comparison Tool

> "Compare TCS, Infosys, and Wipro" triggers `compare_stocks` with all three tickers. The tool fetches data for all three stocks and returns a ranked comparison with automatic winner detection.

![Compare Stocks](screenshots/compare_stocks.png)

**What this demonstrates:**
- `compare_stocks` called with `{"tickers": ["TCS.NS", "INFY.NS", "WIPRO.NS"]}`
- **Live prices: TCS ₹2,410 | Infosys ₹1,248 | Wipro ₹197**
- Automatic rankings: best day performance, 52-week strongest, lowest P/E ratio
- The LLM contextualises: Wipro has highest 52-week strength and lowest P/E

---

### 5. MCP Prompt Template in Action — Deep Analysis Report

> Typing `analyse RELIANCE.NS` retrieves the `stock_analysis_prompt` template from the server, fills in the `{{ticker}}` and `{{timeframe}}` placeholders, then auto-calls two tools to gather data before generating an 8-section structured report.

![Reliance Analysis Report](screenshots/reliance_analysis.png)

**What this demonstrates:**
- Client calls `get_prompt("stock_analysis_prompt", {"ticker": "RELIANCE.NS", "timeframe": "medium-term"})` on the server
- Server fills the template and returns structured message content
- Two tools are auto-invoked: `analyse_fundamentals` + `search_news`
- LLM generates a comprehensive report with real data:
  - Current price: ₹1,380.70 (+0.25%)
  - P/E: 22.47 vs sector avg 20.12
  - ROE: 0.6% (below 15% ideal — flagged as concern)
  - 52W range: ₹1,142 to ₹1,611 (bullish trend confirmed)
  - News: $300B US refinery announcement, Venezuela oil strategy
  - Verdict: Overvalued given high P/E and P/B vs sector

This is the most powerful feature — **MCP Prompts enable reproducible, server-defined AI workflows** that any client can invoke with just a name and arguments.

---

## 🧠 What is MCP? My Understanding

After completing the Anthropic Academy MCP course and building this project end-to-end, here is my deep understanding of MCP:

### The Problem MCP Solves

Before MCP, every AI application built its own custom integration layer between the LLM and external tools. Building Claude access to a database? Custom code. Want GPT-4 to access the same database? Rewrite it differently. No standard existed.

**MCP is the USB-C of AI tool integrations** — a universal standard so any MCP-compatible client (Claude Desktop, custom Python clients, VS Code extensions, IDEs) can talk to any MCP-compatible server (databases, APIs, file systems, SaaS tools) using the same protocol, without custom glue code.

### The Three MCP Primitives

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP PRIMITIVES                               │
├─────────────────┬───────────────────────┬───────────────────────────┤
│   TOOLS         │   RESOURCES           │   PROMPTS                 │
│                 │                       │                           │
│ "Do something"  │ "Know something"      │ "Template something"      │
│                 │                       │                           │
│ Functions the   │ Static/semi-static    │ Reusable, parameterised   │
│ LLM can call.   │ context the server    │ message templates stored  │
│ Like API calls. │ exposes. Read once,   │ on the server. Client     │
│ Has side        │ injected into LLM     │ retrieves + fills with    │
│ effects.        │ context window.       │ arguments at runtime.     │
│                 │                       │                           │
│ Example here:   │ Example here:         │ Example here:             │
│ get_stock_price │ nse_symbols.json      │ stock_analysis_prompt     │
│ search_news     │ market_glossary.md    │ portfolio_review_prompt   │
└─────────────────┴───────────────────────┴───────────────────────────┘
```

### How MCP Communication Works (stdio transport)

```
CLIENT                          SERVER
  │                               │
  │──── spawn as subprocess ─────>│  (python server/finsight_server.py)
  │                               │
  │──── initialize request ──────>│
  │<─── initialize response ──────│  (server capabilities)
  │                               │
  │──── tools/list ──────────────>│
  │<─── [Tool, Tool, Tool] ───────│
  │                               │
  │──── resources/list ──────────>│
  │<─── [Resource, Resource] ─────│
  │                               │
  │──── tools/call ──────────────>│  {name: "get_stock_price",
  │     (when user asks price)     │   arguments: {ticker: "TCS.NS"}}
  │<─── TextContent (JSON) ───────│  (yfinance fetches live data)
  │                               │
  │──── resources/read ──────────>│  uri: "file://portfolio_template"
  │<─── TextContent (file) ───────│  (portfolio file contents)
  │                               │
  │──── prompts/get ─────────────>│  {name: "stock_analysis_prompt",
  │                               │   arguments: {ticker: "RELIANCE.NS"}}
  │<─── GetPromptResult ──────────│  (filled template as messages)

All messages: JSON-RPC 2.0 format over stdin/stdout pipes
```

---

## 🏗️ Architecture and Flow Diagram

### Full System Architecture

```
╔═══════════════════════════════════════════════════════════════════════╗
║                     FINSIGHT MCP — FULL ARCHITECTURE                  ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   ┌────────────────────────────────────────────────────────────┐     ║
║   │                      USER (Terminal)                        │     ║
║   │     "What is the current price of TCS?"                     │     ║
║   └─────────────────────────┬──────────────────────────────────┘     ║
║                             │                                         ║
║   ┌─────────────────────────▼──────────────────────────────────┐     ║
║   │              MCP CLIENT  (finsight_client.py)               │     ║
║   │                                                              │     ║
║   │   ┌──────────────────────┐   ┌───────────────────────────┐ │     ║
║   │   │   Keyword Router     │   │   Ollama (llama3.2)        │ │     ║
║   │   │   (FAST PATH)        │   │   Local LLM (SLOW PATH)   │ │     ║
║   │   │                      │   │                           │ │     ║
║   │   │  Detects: price,     │   │  Interprets complex       │ │     ║
║   │   │  compare, news       │   │  queries. Generates       │ │     ║
║   │   │  queries directly    │   │  tool call JSON.          │ │     ║
║   │   │  from user text      │   │  Auto-fixes arg names.    │ │     ║
║   │   └──────────┬───────────┘   └─────────────┬─────────────┘ │     ║
║   │              └──────────────┬───────────────┘               │     ║
║   │                             │ decides which MCP call         │     ║
║   └─────────────────────────────┼──────────────────────────────┘     ║
║                                 │ JSON-RPC 2.0 over stdio             ║
║   ┌─────────────────────────────▼──────────────────────────────┐     ║
║   │              MCP SERVER  (finsight_server.py)               │     ║
║   │                                                              │     ║
║   │  ┌─────────────────┐ ┌──────────────────┐ ┌─────────────┐ │     ║
║   │  │     TOOLS        │ │    RESOURCES      │ │   PROMPTS   │ │     ║
║   │  │                  │ │                  │ │             │ │     ║
║   │  │ get_stock_price  │ │ nse_symbols.json │ │ stock_      │ │     ║
║   │  │ search_news      │ │ market_glossary  │ │ analysis_   │ │     ║
║   │  │ analyse_         │ │ .md              │ │ prompt      │ │     ║
║   │  │ fundamentals     │ │ portfolio_       │ │             │ │     ║
║   │  │ compare_stocks   │ │ template.txt     │ │ portfolio_  │ │     ║
║   │  └────────┬─────────┘ └────────┬─────────┘ │ review_     │ │     ║
║   │           │                    │ read_text()│ prompt      │ │     ║
║   └───────────┼────────────────────┼────────────┴─────────────┘     ║
║               │                    │                                   ║
║   ┌───────────▼────────┐  ┌────────▼──────────────────────────┐     ║
║   │  yfinance          │  │  Local filesystem                  │     ║
║   │  Yahoo Finance API │  │  (JSON / Markdown / Text files)    │     ║
║   │  NewsAPI free tier │  └───────────────────────────────────┘     ║
║   └────────────────────┘                                             ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

### Request Flow — Simple Price Query

```
USER: "What is the current price of TCS?"
          │
          ▼
┌─────────────────────────────────────────┐
│  STEP 1: Keyword Router                  │
│                                          │
│  Detects trigger word: "price"           │
│  Detects company name: "tcs"             │
│  Maps to ticker: "TCS.NS"                │
│                                          │
│  Builds direct tool call:                │
│  { name: "get_stock_price",              │
│    arguments: { ticker: "TCS.NS" } }     │
│                                          │
│  ✓ No LLM needed for this step           │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  STEP 2: MCP Tool Call (JSON-RPC)        │
│                                          │
│  Client → Server:                        │
│  { method: "tools/call",                 │
│    params: { name: "get_stock_price",    │
│              arguments: {ticker:"TCS.NS"}│
│            }                             │
│  }                                       │
└───────────────────┬─────────────────────┘
                    │ stdio pipe
                    ▼
┌─────────────────────────────────────────┐
│  STEP 3: Server Executes Tool            │
│                                          │
│  finsight_server.py:                     │
│  call_tool("get_stock_price",            │
│            {"ticker": "TCS.NS"})         │
│      ↓                                   │
│  tools/stock_price.py:                   │
│  yf.Ticker("TCS.NS").info                │
│  → Live data from Yahoo Finance          │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  STEP 4: Tool Returns Structured JSON    │
│                                          │
│  { "ticker": "TCS.NS",                   │
│    "company_name": "Tata Consultancy...",│
│    "current_price": 2410.5,              │
│    "price_change_pct": -1.31,            │
│    "market_cap_formatted": "₹8.72 Lakh Cr"│
│    "status": "success" }                 │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  STEP 5: LLM Summarises the JSON         │
│                                          │
│  Ollama (llama3.2) receives:             │
│  - Tool result JSON                      │
│  - Instruction: "Summarise clearly"      │
│                                          │
│  Generates natural language response     │
└───────────────────┬─────────────────────┘
                    │
                    ▼
OUTPUT: "TCS (Tata Consultancy Services) is trading at
         ₹2,410.50, down ₹31.90 (−1.31%) today on NSE."
```

---

### Prompt Template Flow — `analyse RELIANCE.NS`

```
USER: "analyse RELIANCE.NS"
          │
          ▼
┌──────────────────────────────────────────┐
│  Client calls prompts/get on server       │
│                                           │
│  session.get_prompt(                      │
│    "stock_analysis_prompt",               │
│    { "ticker": "RELIANCE.NS",             │
│      "timeframe": "medium-term" }         │
│  )                                        │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  Server fills the template               │
│                                           │
│  stock_analysis.txt contains:            │
│  "Perform a {{timeframe}} analysis       │
│   of the stock: {{ticker}} ..."          │
│                                           │
│  After substitution:                     │
│  "Perform a medium-term analysis         │
│   of the stock: RELIANCE.NS ..."         │
│                                           │
│  Returns as PromptMessage (role: user)   │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  Client auto-gathers supporting data     │
│                                           │
│  Tool 1: analyse_fundamentals            │
│  → P/E, ROE, EPS, margins, debt ratios   │
│                                           │
│  Tool 2: search_news                     │
│  → Latest 5 headlines about Reliance     │
│                                           │
│  Both results injected into LLM context  │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│  Ollama generates the 8-section report   │
│                                           │
│  Input: prompt template +                │
│         fundamentals JSON +              │
│         news JSON                        │
│                                           │
│  Output: Structured analysis with        │
│  company snapshot, valuation, financials,│
│  technicals, news, verdict, target price │
└────────────────────┬─────────────────────┘
                     │
                     ▼
RESULT: Full structured investment analysis
        report with live data and context
```

---

## 🧩 MCP Primitives Implemented

### Tools (4 total)

Tools are **executable functions** with strict JSON Schema validation. The LLM reads the schema to understand what arguments to pass.

| Tool | Arguments | Data Source | What it returns |
|------|-----------|-------------|-----------------|
| `get_stock_price` | `ticker: string` | yfinance | Current price, change %, volume, market cap |
| `search_news` | `query: string`, `max_results: int` | NewsAPI / yfinance | Latest headlines with source and date |
| `analyse_fundamentals` | `ticker: string` | yfinance | P/E, P/B, ROE, EPS, margins, debt ratios, 52W range |
| `compare_stocks` | `tickers: string[]` | yfinance | Side-by-side comparison + auto-rankings |

```python
# How a tool is registered on the server
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_stock_price",
            description="Fetch the current live price for an Indian NSE stock. "
                        "Use NSE ticker format: TCS.NS, RELIANCE.NS, INFY.NS",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "NSE ticker symbol e.g. TCS.NS"
                    }
                },
                "required": ["ticker"]
            }
        )
    ]
```

---

### Resources (3 total)

Resources are **read-only context files**. They don't execute — they provide knowledge injected into the LLM's context window.

| URI | File | Content | Used for |
|---|---|---|---|
| `file://nse_symbols` | `nse_symbols.json` | 50 NSE tickers + sectors | LLM knows what tickers exist |
| `file://market_glossary` | `market_glossary.md` | 30+ finance term definitions | LLM explains terms accurately |
| `file://portfolio_template` | `portfolio_template.txt` | 7-stock sample portfolio | Portfolio review command |

```python
# Resource is loaded once at startup and injected as system context
portfolio_res = await session.read_resource("file://portfolio_template")
messages.append({
    "role": "system",
    "content": f"USER'S PORTFOLIO:\n{portfolio_text}"
    # Now the LLM knows the user's holdings for the entire session
})
```

**Key insight:** Resources avoid re-fetching static data on every request. The glossary and symbol list are loaded once into the LLM's memory — reducing latency and API calls.

---

### Prompts (2 total)

Prompts are **parameterised workflow templates** stored on the server. They represent the most powerful (and most underused) MCP primitive.

| Prompt | Arguments | Template produces |
|---|---|---|
| `stock_analysis_prompt` | `ticker`, `timeframe` | 8-section structured analysis format |
| `portfolio_review_prompt` | `risk_profile` | Portfolio score + buy/hold/sell table |

```python
# Prompt with argument placeholders on the server
@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    template = Path("prompts/stock_analysis.txt").read_text()
    filled = template.replace("{{ticker}}", arguments["ticker"])
    filled = filled.replace("{{timeframe}}", arguments.get("timeframe", "medium-term"))
    return types.GetPromptResult(
        messages=[PromptMessage(role="user", content=TextContent(text=filled))]
    )
```

**Why prompts matter:** They encode **standardised AI workflows** on the server side. Any MCP client — whether it's Claude Desktop, a custom Python client, or a VS Code extension — can trigger the same deep analysis workflow just by calling `get_prompt("stock_analysis_prompt", {"ticker": "TCS.NS"})`.

---

## 📁 Project Structure

```
finsight-mcp/
│
├── server/                          ← MCP Server (the "what")
│   ├── finsight_server.py           ← Main server: tools + resources + prompts
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── stock_price.py           ← get_stock_price (yfinance)
│   │   ├── news_search.py           ← search_news (NewsAPI + yfinance fallback)
│   │   ├── fundamentals.py          ← analyse_fundamentals (50+ metrics)
│   │   └── compare_stocks.py        ← compare_stocks (multi-ticker)
│   └── resources/
│       ├── nse_symbols.json         ← 50 NSE tickers with sectors
│       ├── market_glossary.md       ← Finance term definitions
│       └── portfolio_template.txt   ← Sample user portfolio
│
├── client/
│   └── finsight_client.py           ← Custom MCP client (the "how")
│                                       Keyword router + Ollama + arg-fixer
│
├── prompts/
│   ├── stock_analysis.txt           ← 8-section analysis template
│   └── portfolio_review.txt         ← Portfolio review template
│
├── tests/
│   └── test_tools.py                ← Unit tests for all 4 tools
│
├── .env.example                     ← Config template
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack (100% Free)

| Component | Technology | Cost |
|---|---|---|
| MCP Framework | `mcp` Python SDK (official Anthropic) | Free |
| Local LLM | Ollama + llama3.2 (runs on M1 Mac) | Free |
| Stock Data | `yfinance` Yahoo Finance | Free |
| News | NewsAPI free tier + yfinance fallback | Free |
| Terminal UI | `rich` | Free |
| HTTP Client | `httpx` (async) | Free |
| Config | `python-dotenv` | Free |

**Total monthly cost to run: ₹0**

---

## 🚀 Setup and Installation (macOS M1)

### Step 1 — Install Prerequisites

```bash
# Homebrew (package manager)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python 3.11
brew install python@3.11

# Ollama (local LLM runtime)
brew install ollama

# Node.js (for MCP Inspector)
brew install node
```

### Step 2 — Project Setup

```bash
git clone https://github.com/YOUR_USERNAME/finsight-mcp.git
cd finsight-mcp

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### Step 3 — Download the LLM Model (one-time)

```bash
# Terminal 1: start Ollama (keep running)
ollama serve

# Terminal 2: download the model (~2GB)
ollama pull llama3.2
ollama list   # Verify it appears
```

---

## ▶️ How to Run

### Full Chat Client

```bash
# Terminal 1
ollama serve

# Terminal 2
source venv/bin/activate
python client/finsight_client.py
```

**Commands inside the chat:**

| Command | What happens |
|---|---|
| `tools` | Lists all tools, resources, prompts from server |
| `What is the price of TCS?` | Calls `get_stock_price` tool |
| `Compare TCS and Infosys` | Calls `compare_stocks` tool |
| `News about Reliance` | Calls `search_news` tool |
| `analyse RELIANCE.NS` | Uses `stock_analysis_prompt` template |
| `portfolio` | Uses `portfolio_review_prompt` template |
| `What does P/E mean?` | LLM answers using glossary resource context |

### MCP Inspector

```bash
npx @modelcontextprotocol/inspector python server/finsight_server.py
# Open http://localhost:5173 in browser
```

### Run Tests

```bash
python tests/test_tools.py
```

---

## 🔑 Key Implementation Details

### Dual-Path Tool Routing

The most important engineering decision. Local LLMs sometimes generate wrong argument names (e.g., `{"param": "TCS.NS"}` instead of `{"ticker": "TCS.NS"}`). I solved this with two layers:

```python
# FAST PATH — keyword detection, no LLM needed
direct = detect_tool_from_user_input(user_input)
if direct:
    result = await session.call_tool(direct["name"], direct["arguments"])

# SLOW PATH — LLM decides, with auto-fix for wrong arg names
else:
    llm_response = await call_ollama(messages)
    tool_call = extract_tool_call(llm_response)  # also remaps wrong keys
    result = await session.call_tool(...)
```

The `extract_tool_call()` function auto-remaps common LLM mistakes:
```python
# If LLM sends {"param": "TCS.NS"}, remap to {"ticker": "TCS.NS"}
wrong_keys = {"param", "symbol", "stock", "ticker_symbol", "stock_ticker"}
for wrong in wrong_keys:
    if wrong in args and "ticker" not in args:
        args["ticker"] = args.pop(wrong)
```

### Context Window Management

Multi-turn conversations exceed the LLM's context limit. Solution: always preserve system prompts, trim old messages.

```python
if len(messages) > 22:
    messages = messages[:2] + messages[-20:]   # keep 2 system prompts + last 20
```

### Portfolio Resource Injection

The portfolio is loaded once at startup and stays in context for the full session:

```python
portfolio = await session.read_resource("file://portfolio_template")
messages.append({"role": "system", "content": f"USER PORTFOLIO:\n{portfolio}"})
# LLM now knows all 7 holdings throughout the conversation
```

---

## 📊 Outcomes and Results

### All Features Verified Working

| Feature | MCP Primitive | Status | Actual Output |
|---|---|---|---|
| Live stock price | Tool | ✅ | TCS ₹2,410.50 (−1.31%) |
| Stock comparison | Tool | ✅ | TCS vs Infosys vs Wipro table |
| Fundamentals analysis | Tool | ✅ | P/E 22.47, ROE 0.6%, 52W range |
| News search | Tool | ✅ | Recent headlines with sources |
| NSE symbol lookup | Resource | ✅ | 50 companies loaded in context |
| Finance glossary | Resource | ✅ | LLM explains terms correctly |
| Portfolio context | Resource | ✅ | 7 holdings loaded at startup |
| Deep analysis report | Prompt | ✅ | 8-section Reliance report |
| Portfolio review | Prompt | ✅ | Score + buy/hold/sell table |
| MCP Inspector | All 3 | ✅ | All primitives browsable |

### Reliance Industries Report — Actual Output Summary

The `analyse RELIANCE.NS` command produced a complete report including:
- **Price:** ₹1,380.70 (+0.25%), trading in narrow range
- **Valuation:** P/E 22.47 (above sector avg 20.12 — slightly overvalued)
- **Financial health:** ROE 0.6% below 15% ideal, D/E 35.65 (high leverage)
- **Technicals:** Bullish — above both 50 DMA (₹1,420) and 200 DMA (₹1,448)
- **News catalysts:** $300B US refinery announcement, Venezuela oil strategy
- **Verdict:** Overvalued on P/E and P/B basis vs sector peers

---

## 📚 What I Learned

### 1. MCP Transport Layer
The stdio transport works by spawning the server as a subprocess and using stdin/stdout pipes for JSON-RPC 2.0 messages. Server errors go to stderr (visible in terminal), MCP messages go to stdout. Understanding this separation was key to debugging.

### 2. Tool Schema Quality Determines LLM Behaviour
The JSON Schema is what the LLM reads to understand how to call a tool. Vague schemas lead to wrong argument names. I learned to always include concrete examples in the description — `"e.g. TCS.NS, RELIANCE.NS"` — not just abstract descriptions.

### 3. Resources vs Tools — The Right Choice
Resources = context that doesn't change per request (glossary, symbol lists, user profile). Tools = actions with real-time data or side effects. Using a tool to serve a static glossary would add unnecessary latency. Using a resource for live stock prices would return stale data.

### 4. Prompt Templates Enable Composable AI Workflows
Server-side prompts let you define **standardised workflows** once and trigger them from any MCP client. The stock analysis workflow (template + 2 tool calls + LLM generation) can be triggered from Claude Desktop, a custom client, or any future MCP client — without rewriting the workflow logic.

### 5. Local LLMs Require Defensive Engineering
`llama3.2` is excellent on M1 but occasionally generates wrong argument names. I implemented both a keyword router and an auto-fixer — teaching me that production agentic systems need **output validation and fallback strategies**, especially with smaller local models.

### 6. The Server-Client Separation is the Core Value
The MCP server doesn't know Ollama exists. The client doesn't know yfinance exists. They communicate only through the MCP protocol. This means: swap Ollama for Claude API → zero server changes. Swap yfinance for Bloomberg → zero client changes. This modular separation is what makes MCP powerful for production systems.

---

## 🔮 Possible Extensions

- **Web UI** — Replace terminal with Streamlit/FastAPI interface
- **Historical charts** — Add `get_price_history` tool with matplotlib
- **BSE support** — Add BSE-listed stocks alongside NSE
- **Portfolio P&L** — Track actual buy prices and show real gain/loss
- **SSE transport** — Deploy server remotely (not just local stdio)
- **Claude API** — Replace Ollama with Anthropic Claude for production
- **Multi-server client** — Connect to multiple MCP servers simultaneously

---

## ⚠️ Disclaimer

For educational purposes only. Nothing produced by this application constitutes financial advice. Consult a SEBI-registered investment advisor before any investment decisions.

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

**Built to demonstrate complete Model Context Protocol (MCP) implementation skills.**

*Completed after the Anthropic Academy — Introduction to MCP course*

If this helped you understand MCP, give it a ⭐

</div>