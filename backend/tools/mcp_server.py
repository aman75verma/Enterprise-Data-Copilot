from typing import Any

from mcp.server.fastmcp import FastMCP

from backend.tools.docs_tool import search_docs as search_docs_impl
from backend.tools.issue_tracker_tool import check_issue_tracker as check_issue_tracker_impl
from backend.tools.sql_tool import query_customer_db as query_customer_db_impl

mcp = FastMCP("enterprise-data-copilot")


@mcp.tool(
    name="query_customer_db",
    description=(
        "Run a read-only SQL query against the customer support database "
        "(customers, organizations, projects, usage_metrics, subscriptions, invoices, "
        "tickets, ticket_messages, agents tables). Use for questions about a specific "
        "customer, project, organization, billing, or ticket history."
    ),
)
def query_customer_db(sql_query: str) -> dict[str, Any]:
    return query_customer_db_impl(sql_query)


@mcp.tool(
    name="search_docs",
    description=(
        "Search product documentation for how-to guides, feature explanations, and setup "
        "instructions. Use for general product knowledge questions not tied to a specific "
        "customer's account."
    ),
)
def search_docs(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    return search_docs_impl(query=query, top_k=top_k)


@mcp.tool(
    name="check_issue_tracker",
    description=(
        "Check the live issue tracker for open bugs or feature requests matching a keyword, "
        "or look up a specific issue by number. Use when a customer reports a bug and you "
        "need to check if it's a known issue."
    ),
)
def check_issue_tracker(keyword: str | None = None, issue_number: int | None = None) -> dict[str, Any]:
    return check_issue_tracker_impl(keyword=keyword, issue_number=issue_number)


if __name__ == "__main__":
    mcp.run()
