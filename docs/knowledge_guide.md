# Enterprise Data Copilot — Knowledge Guide

> How the tools, orchestrator, MCP server, and dual-path architecture work together.

---

## 1. The Three Core Tools

Every feature in this Copilot ultimately calls one of three tool **implementations**. These are plain Python functions with zero awareness of MCP or LLMs.

### 1.1 `query_customer_db` — [sql_tool.py](../backend/tools/sql_tool.py)

| What | Details |
|------|---------|
| **Input** | `sql_query: str` (a SQL string) |
| **Output** | `{"columns": [...], "rows": [...], "row_count": N, "truncated": bool}` |
| **Safety** | Rejects anything that isn't a `SELECT` — blocks INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, COPY, CALL. Uses regex on the query **after** stripping string literals so `WHERE name = 'drop'` is safe. Also sets `readonly=True` on the psycopg2 session and `statement_timeout = 5000ms`. |
| **Max rows** | 100 (returns `truncated: true` if more exist) |

### 1.2 `search_docs` — [docs_tool.py](../backend/tools/docs_tool.py)

| What | Details |
|------|---------|
| **Input** | `query: str`, `top_k: int` (1–10, default 5) |
| **Output** | List of `{title, source_file, url, product, section, chunk_index, content}` |
| **How it works** | Encodes the query using `sentence-transformers/all-MiniLM-L6-v2` (384-dim), then runs a cosine-distance (`<->`) search against the `doc_chunks` table via `pgvector`. The embedding model is loaded once via `@lru_cache`. |

### 1.3 `check_issue_tracker` — [issue_tracker_tool.py](../backend/tools/issue_tracker_tool.py)

| What | Details |
|------|---------|
| **Input** | `keyword: str` OR `issue_number: int` (at least one required) |
| **Output** | `{"mode": "keyword"/"issue_number", "results"/"result": [...]}` |
| **How it works** | Delegates to `LiveIssueTrackerClient` ([github_issues.py](../backend/api/github_issues.py)), which hits the GitHub REST API (`/search/issues` or `/repos/supabase/supabase/issues/{n}`). Returns summary objects with number, title, state, labels, URL, timestamps, and comment count. |

### Where tool definitions live (single source of truth)

All tool names, descriptions, and parameter schemas are defined **once** in:

```
backend/tools/tool_registry.py
```

Both the orchestrator and MCP server import from this file. If you ever add a 4th tool, update `tool_registry.py` and both paths pick it up automatically.

---

## 2. Path A: The Orchestrator (Direct LLM Loop)

**File:** [orchestrator.py](../backend/agent/orchestrator.py)

### How it works (step by step)

```
User question
    │
    ▼
┌──────────────────────────────────────┐
│ 1. Build message stack:              │
│    - system_prompt.py (SYSTEM_PROMPT)│
│    - conversation_history (if any)   │
│    - user message                    │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ 2. Send to Groq API                 │
│    model = llama-3.3-70b-versatile   │
│    tools = TOOLS (from registry)     │
│    tool_choice = "auto"              │
└──────────────┬───────────────────────┘
               │
        ┌──────┴──────┐
        │             │
   tool_calls    no tool_calls
        │             │
        ▼             ▼
┌───────────┐   ┌────────────┐
│ 3. Dispatch│   │ Return     │
│ _execute   │   │ answer     │
│ _tool()    │   └────────────┘
└─────┬─────┘
      │  calls the Python function directly
      │  (no HTTP, no network)
      ▼
┌──────────────────────────────────────┐
│ 4. Append tool result to messages    │
│    role="tool", tool_call_id=...     │
│    Loop back to step 2               │
│    (max 5 rounds)                    │
└──────────────────────────────────────┘
```

### Key design choices

- **Direct Python imports** — the orchestrator calls `sql_tool.query_customer_db(...)` directly. No HTTP. No serialization. Fastest possible path.
- **Multi-tool support** — if the LLM emits 2+ tool calls in one turn (e.g., "check the customer's plan AND look up the bug"), they are all executed before the next LLM call.
- **Sequential loops** — the LLM can call tools in round 1, get results, then call *different* tools in round 2. Capped at 5 rounds for safety.
- **Structured logging** — every tool call is logged with latency via `log_tool_call()`.

### How the frontend uses it

The orchestrator exposes one function:

```python
from backend.agent.orchestrator import run_agent

result = run_agent(
    user_message="What plan is jane@acme.com on?",
    conversation_history=[]   # pass previous turns for multi-turn chat
)

result["answer"]      # "Jane is on the Pro plan..."
result["tool_calls"]  # [{"tool": "query_customer_db", "arguments": {...}, "result": {...}}]
result["history"]     # full message history for the next turn
```

A FastAPI endpoint wraps this in an HTTP route (`POST /chat`) for the React frontend. The frontend sends JSON, gets back the answer + tool call trace for display.

---

## 3. Path B: The MCP Server

**File:** [mcp_server.py](../backend/tools/mcp_server.py)

### MCP Basics

**MCP (Model Context Protocol)** is a standard for exposing tools to LLMs over a network. Think of it as "REST for AI tools."

| Concept | What it means |
|---------|---------------|
| **Server** | A process that registers tools and listens for calls |
| **Client** | Any process that discovers and invokes those tools |
| **Tool** | A function with a name, description, and JSON parameter schema |
| **Transport** | How client/server communicate — `stdio` (pipes) or `SSE` (HTTP) |

### What the `@mcp.tool` decorator does

```python
@mcp.tool(
    name="search_docs",
    description="Search product documentation..."
)
def search_docs(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    return search_docs_impl(query=query, top_k=top_k)
```

This decorator:
1. **Registers** the function with the `FastMCP` instance
2. **Generates a JSON schema** from the Python type hints (`query: str` → `{"type": "string"}`)
3. **Publishes** the tool so any MCP client can discover it and call it

### Why the wrapper function exists

The decorator needs a function to register. But the real logic lives in `docs_tool.py`. So:

```
@mcp.tool decorator → wrapper function → docs_tool.search_docs (real implementation)
```

This keeps the MCP layer **thin** — it's just transport. All business logic stays in the dedicated tool modules.

### How to use MCP in our frontend

**Option 1: Our React frontend talks to FastAPI, which calls the orchestrator directly (current setup).**

```
React UI  →  POST /chat  →  FastAPI  →  orchestrator.run_agent()  →  tools
```

**Option 2: Our React frontend talks to FastAPI, which talks to the MCP server.**

```
React UI  →  POST /chat  →  FastAPI  →  MCP Client  →  MCP Server  →  tools
```

Both options call the same tool implementations. Option 1 is faster (no network hop). Option 2 is more decoupled (the tools could run on a separate machine).

### How other sites / apps use our tools via MCP

Any external system can connect to the MCP server:

```python
# External app (any language with MCP SDK)
from mcp.client import MCPClient

client = MCPClient("enterprise-data-copilot")

# Discover available tools
tools = client.get_tools()
# → [{"name": "query_customer_db", ...}, {"name": "search_docs", ...}, ...]

# Call a tool
result = client.call("search_docs", {"query": "enable RLS", "top_k": 3})
```

Or via raw HTTP:

```bash
# Discover tools
curl http://localhost:5000/tools

# Call a tool
curl -X POST http://localhost:5000/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "search_docs", "args": {"query": "enable RLS", "top_k": 3}}'
```

### Starting the MCP server

```powershell
.\venv\Scripts\python.exe -m backend.tools.mcp_server
```

---

## 4. Orchestrator vs MCP — Comparison

| Dimension | Orchestrator (Direct) | MCP Server (Network) |
|-----------|-----------------------|----------------------|
| **Latency** | ~0ms overhead (in-process function call) | +network round-trip (HTTP/stdio) |
| **Coupling** | Tightly coupled — orchestrator imports the tool functions | Loosely coupled — client only knows the JSON schema |
| **Scalability** | Scales with the FastAPI process | Can run on a separate machine / container |
| **Language support** | Python only | Any language with MCP SDK (Python, JS, Go, etc.) |
| **Multi-consumer** | Single consumer (the orchestrator) | Multiple consumers can connect simultaneously |
| **Testing** | Unit-test the Python functions directly | Integration-test via HTTP (mimics real client behavior) |
| **When to use** | UI backend (speed matters) | External integrations, microservices, CLI demos |

### Running the comparison script

```powershell
.\venv\Scripts\python.exe -m backend.agent.compare
```

This runs the same 3 tool calls through the direct path and prints latency for each.

---

## 5. New Features Added (Standardization Pass)

| Feature | File | Purpose |
|---------|------|---------|
| **Tool Registry** | [tool_registry.py](../backend/tools/tool_registry.py) | Single source of truth for all tool schemas. Both orchestrator and MCP server import from here — descriptions can never drift. |
| **Structured Logger** | [logger.py](../backend/agent/logger.py) | Logs every tool call with: tool name, arguments, result preview, latency (ms), and execution path (direct/mcp). Uses a context manager for clean timing. |
| **DB Connection Pool** | [pool.py](../backend/db/pool.py) | `ThreadedConnectionPool` (1–10 connections). Tools no longer create a new TCP connection per request. |
| **Error Types** | [errors.py](../backend/tools/errors.py) | `ToolError` base class with `tool_name` and `message`. Gives both paths a uniform way to catch and report failures. |
| **Comparison Runner** | [compare.py](../backend/agent/compare.py) | Runs the same tool call through both paths, prints latency and results side by side. |

---

## 6. File Map (Quick Reference)

```
backend/
├── agent/
│   ├── system_prompt.py    # LLM system prompt (schema context)
│   ├── orchestrator.py     # Path A: LLM loop (Groq + direct tool calls)
│   ├── logger.py           # Structured logging with latency
│   └── compare.py          # Dual-path comparison runner
├── tools/
│   ├── tool_registry.py    # Single source of truth for tool schemas
│   ├── errors.py           # Standardized ToolError base class
│   ├── sql_tool.py         # query_customer_db implementation
│   ├── docs_tool.py        # search_docs implementation
│   ├── issue_tracker_tool.py  # check_issue_tracker implementation
│   ├── mcp_server.py       # Path B: MCP server (wraps tools for network access)
│   └── demo_tools.py       # CLI demo runner
├── api/
│   └── github_issues.py    # LiveIssueTrackerClient (GitHub REST API)
├── db/
│   ├── schema.sql          # Database schema
│   ├── seed.py             # Story-driven data generator
│   ├── ingest_docs.py      # RAG corpus ingestion
│   └── pool.py             # Shared DB connection pool
└── .env                    # Secrets (GROQ_API_KEY, DATABASE_URL, etc.)
```
