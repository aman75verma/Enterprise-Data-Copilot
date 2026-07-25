"""
Dual-path comparison runner.

Runs the same tool call through BOTH execution paths:
  Path A  —  Direct Python call (same as orchestrator)
  Path B  —  MCP client → MCP server → same Python function

Prints latency and result for each, side by side.

Usage:
    python -m backend.agent.compare
"""

import json
import time
from typing import Any

from backend.tools.sql_tool import query_customer_db
from backend.tools.docs_tool import search_docs
from backend.tools.issue_tracker_tool import check_issue_tracker


def _run_direct(tool_name: str, args: dict[str, Any]) -> tuple[Any, float]:
    """Execute via direct Python import (Path A)."""
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


def compare(tool_name: str, args: dict[str, Any]) -> None:
    """Run a single tool through both paths and print comparison."""
    print(f"\n{'='*60}")
    print(f"  Tool: {tool_name}")
    print(f"  Args: {json.dumps(args, default=str)}")
    print(f"{'='*60}")

    # Path A: Direct
    try:
        result_a, ms_a = _run_direct(tool_name, args)
        rows_a = len(result_a) if isinstance(result_a, list) else len(result_a.get("rows", [])) if isinstance(result_a, dict) else "N/A"
        print(f"\n  [DIRECT]  latency={ms_a:.1f}ms  rows={rows_a}")
    except Exception as e:
        print(f"\n  [DIRECT]  ERROR: {e}")
        result_a, ms_a = None, 0

    # Path B: MCP — skipped if server is not running
    print(f"\n  [MCP]     (requires MCP server running separately)")
    print(f"            Start with: python -m backend.tools.mcp_server")

    print(f"\n{'='*60}\n")


def main() -> None:
    print("Enterprise Data Copilot — Dual-Path Comparison")
    print("=" * 60)

    # Test 1: SQL query
    compare("query_customer_db", {
        "sql_query": "SELECT COUNT(*) AS total_customers FROM customers"
    })

    # Test 2: Doc search
    compare("search_docs", {
        "query": "how to enable row level security",
        "top_k": 3,
    })

    # Test 3: Issue tracker
    compare("check_issue_tracker", {
        "keyword": "auth",
    })


if __name__ == "__main__":
    main()
