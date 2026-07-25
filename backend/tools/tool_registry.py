"""
Tool Registry — Single source of truth for tool definitions.

Both the orchestrator (Groq function-calling schema) and the MCP server
import from here, so names, descriptions, and parameter schemas never drift.
"""

from typing import Any

# ------------------------------------------------------------------
# Canonical tool definitions
# ------------------------------------------------------------------
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "query_customer_db",
        "description": (
            "Run a read-only SQL query against the customer support database "
            "(customers, organizations, projects, usage_metrics, subscriptions, "
            "invoices, tickets, ticket_messages, agents). Use for questions about "
            "a specific customer, project, organization, billing, or ticket history."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": "A read-only SELECT query",
                }
            },
            "required": ["sql_query"],
        },
    },
    {
        "name": "search_docs",
        "description": (
            "Search product documentation for how-to guides, feature explanations, "
            "and setup instructions. Use for general product knowledge questions "
            "not tied to a specific customer's account."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to return (default 5)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_issue_tracker",
        "description": (
            "Check the live issue tracker for open bugs or feature requests "
            "matching a keyword, or look up a specific issue by number. Use when "
            "a customer reports a bug and you need to check if it's a known issue."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Search keyword (omit if using issue_number)",
                },
                "issue_number": {
                    "type": "integer",
                    "description": "Specific issue number to look up",
                },
            },
        },
    },
]


def get_openai_tools() -> list[dict[str, Any]]:
    """Return the tool list in OpenAI/Groq function-calling format."""
    return [
        {"type": "function", "function": defn}
        for defn in TOOL_DEFINITIONS
    ]


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Look up a single tool definition by name."""
    for defn in TOOL_DEFINITIONS:
        if defn["name"] == name:
            return defn
    return None
