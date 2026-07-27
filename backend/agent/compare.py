"""
Dual-path comparison runner.

Runs the same tool call through BOTH execution paths:
  Path A  —  Direct Python call (same as orchestrator)
  Path B  —  MCP client → MCP server (subprocess) → same Python function

The MCP path spawns the server as a child process over stdio,
calls the tool via the MCP protocol, and measures the round-trip latency.
"""

import asyncio
import json
import sys
import time
from typing import Any

from backend.tools.sql_tool import query_customer_db
from backend.tools.docs_tool import search_docs
from backend.tools.issue_tracker_tool import check_issue_tracker


# ── Path A: Direct Python ──────────────────────────────────

def _run_direct(tool_name: str, args: dict[str, Any]) -> tuple[Any, float]:
    """Execute via direct Python import."""
    dispatch = {
        "query_customer_db": query_customer_db,
        "search_docs": search_docs,
        "check_issue_tracker": check_issue_tracker,
    }
    fn = dispatch[tool_name]
    start = time.perf_counter()
    result = fn(**args)
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed


# ── Path B: MCP Client → MCP Server ───────────────────────

async def _run_mcp_async(tool_name: str, args: dict[str, Any]) -> tuple[Any, float]:
    """
    Spawn the MCP server as a subprocess, connect as an MCP client,
    call the tool, and return the result + latency.
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "backend.tools.mcp_server"],
    )

    start = time.perf_counter()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call the tool over MCP
            response = await session.call_tool(tool_name, arguments=args)

    elapsed = (time.perf_counter() - start) * 1000

    # Parse the MCP response content
    if response.content:
        text = response.content[0].text
        try:
            result = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            result = text
    else:
        result = None

    return result, elapsed


def _run_mcp(tool_name: str, args: dict[str, Any]) -> tuple[Any, float]:
    """Synchronous wrapper around the async MCP client call."""
    return asyncio.run(_run_mcp_async(tool_name, args))


# ── CLI entrypoint ─────────────────────────────────────────

def compare(tool_name: str, args: dict[str, Any]) -> None:
    """Run a single tool through both paths and print comparison."""
    print(f"\n{'='*60}")
    print(f"  Tool: {tool_name}")
    print(f"  Args: {json.dumps(args, default=str)}")
    print(f"{'='*60}")

    # Path A: Direct
    try:
        result_a, ms_a = _run_direct(tool_name, args)
        print(f"\n  [DIRECT]  latency={ms_a:.1f}ms")
    except Exception as e:
        print(f"\n  [DIRECT]  ERROR: {e}")
        ms_a = 0

    # Path B: MCP
    try:
        result_b, ms_b = _run_mcp(tool_name, args)
        print(f"  [MCP]     latency={ms_b:.1f}ms")
    except Exception as e:
        print(f"  [MCP]     ERROR: {e}")
        ms_b = 0

    if ms_a and ms_b:
        overhead = ms_b - ms_a
        print(f"\n  Overhead: +{overhead:.1f}ms ({overhead/ms_a*100:.0f}% slower via MCP)")

    print(f"\n{'='*60}\n")


def main() -> None:
    print("Enterprise Data Copilot — Dual-Path Comparison")
    print("=" * 60)

    compare("query_customer_db", {
        "sql_query": "SELECT COUNT(*) AS total_customers FROM customers"
    })

    compare("search_docs", {
        "query": "how to enable row level security",
        "top_k": 3,
    })

    compare("check_issue_tracker", {
        "keyword": "auth",
    })


if __name__ == "__main__":
    main()
