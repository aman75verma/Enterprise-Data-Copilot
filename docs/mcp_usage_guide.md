# Using Supabase Support Copilot via MCP

This guide shows you how to connect to the MCP server we built and use its tools from **any** MCP-compatible client — Claude Desktop, your own scripts, or other AI agents.

---

## What Is Exposed?

Our MCP server (`backend/tools/mcp_server.py`) exposes three tools over the MCP protocol:

| Tool Name | What It Does |
|---|---|
| `query_customer_db` | Runs a read-only SQL query against the PostgreSQL customer database |
| `search_docs` | Searches the embedded Supabase documentation via vector similarity |
| `check_issue_tracker` | Fetches live open issues from the `supabase/supabase` GitHub repo |

---

## Quick Start: Run the MCP Server

```bash
# From the project root (with venv activated)
python -m backend.tools.mcp_server
```

The server starts on `stdio` transport by default. It speaks JSON-RPC over stdin/stdout.

---

## Connect from Claude Desktop

Add this to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "supabase-copilot": {
      "command": "python",
      "args": ["-m", "backend.tools.mcp_server"],
      "cwd": "C:/Users/ammua/Desktop/Enterprise Data Copilot"
    }
  }
}
```

Restart Claude Desktop. You will see the three tools available in the tool picker.

---

## Connect from a Python Script

```python
import subprocess, json

proc = subprocess.Popen(
    ["python", "-m", "backend.tools.mcp_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    cwd="C:/Users/ammua/Desktop/Enterprise Data Copilot"
)

# Send a JSON-RPC request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "query_customer_db",
        "arguments": {"sql_query": "SELECT COUNT(*) FROM customers"}
    }
}

proc.stdin.write((json.dumps(request) + "\n").encode())
proc.stdin.flush()

response = proc.stdout.readline()
print(json.loads(response))
```

---

## Connect from Another Website / App

If you want to expose MCP tools over HTTP (for a web frontend or third-party app), you have two options:

### Option A: Use Our FastAPI Endpoints (Recommended)
Our FastAPI backend at `http://localhost:8000` already wraps the same tool functions:

```
POST /chat              → AI orchestrator (auto-selects tools)
POST /admin/compare     → Run a specific tool directly
GET  /admin/logs        → View execution history
```

Any frontend can call these with standard `fetch()`.

### Option B: MCP over SSE (Server-Sent Events)
Change the MCP server transport from `stdio` to `sse`:

```python
# In mcp_server.py, change the last line:
mcp.run(transport="sse", port=5050)
```

Then connect from any SSE-compatible MCP client at `http://localhost:5050/sse`.

---

## Tool Schemas (for Reference)

These are the exact schemas registered in `tool_registry.py`:

### query_customer_db
```json
{
  "name": "query_customer_db",
  "parameters": {
    "sql_query": { "type": "string", "description": "Read-only SQL query" }
  }
}
```

### search_docs
```json
{
  "name": "search_docs",
  "parameters": {
    "query": { "type": "string" },
    "top_k": { "type": "integer", "default": 5 }
  }
}
```

### check_issue_tracker
```json
{
  "name": "check_issue_tracker",
  "parameters": {
    "keyword": { "type": "string", "default": "" },
    "issue_number": { "type": "integer", "default": null }
  }
}
```

---

## Summary

| Method | Transport | Best For |
|---|---|---|
| Claude Desktop config | stdio | Personal AI assistant usage |
| Python subprocess | stdio | Scripting and automation |
| FastAPI `/chat` endpoint | HTTP | Web frontends |
| MCP SSE transport | HTTP/SSE | Third-party MCP clients |
