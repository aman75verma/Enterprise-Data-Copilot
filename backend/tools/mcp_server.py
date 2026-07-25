"""
MCP Server — Exposes Copilot tools over the Model Context Protocol.

Tool definitions are imported from the shared tool_registry so they
stay in sync with the orchestrator automatically.
"""

from typing import Any

from mcp.server.fastmcp import FastMCP

from backend.agent.logger import log_tool_call
from backend.tools.sql_tool import query_customer_db as query_customer_db_impl
from backend.tools.docs_tool import search_docs as search_docs_impl
from backend.tools.issue_tracker_tool import check_issue_tracker as check_issue_tracker_impl
from backend.tools.tool_registry import get_tool_by_name

mcp = FastMCP("enterprise-data-copilot")

# Descriptions are pulled from the shared registry
_sql_defn = get_tool_by_name("query_customer_db")
_docs_defn = get_tool_by_name("search_docs")
_issue_defn = get_tool_by_name("check_issue_tracker")


@mcp.tool(name="query_customer_db", description=_sql_defn["description"])
def query_customer_db(sql_query: str) -> dict[str, Any]:
    with log_tool_call("query_customer_db", {"sql_query": sql_query}, path="mcp") as ctx:
        result = query_customer_db_impl(sql_query)
        ctx["result"] = result
    return result


@mcp.tool(name="search_docs", description=_docs_defn["description"])
def search_docs(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    with log_tool_call("search_docs", {"query": query, "top_k": top_k}, path="mcp") as ctx:
        result = search_docs_impl(query=query, top_k=top_k)
        ctx["result"] = result
    return result


@mcp.tool(name="check_issue_tracker", description=_issue_defn["description"])
def check_issue_tracker(keyword: str | None = None, issue_number: int | None = None) -> dict[str, Any]:
    with log_tool_call("check_issue_tracker", {"keyword": keyword, "issue_number": issue_number}, path="mcp") as ctx:
        result = check_issue_tracker_impl(keyword=keyword, issue_number=issue_number)
        ctx["result"] = result
    return result


if __name__ == "__main__":
    mcp.run()
