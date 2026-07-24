"""
Orchestrator — Agentic tool-calling loop using Groq (Llama 3.3 70B).

Handles:
- Single and multi-tool routing
- Sequential tool calls in a loop
- Conversation history
- Structured tool result injection
"""

import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from backend.agent.system_prompt import SYSTEM_PROMPT
from backend.tools.sql_tool import query_customer_db, UnsafeQueryError
from backend.tools.docs_tool import search_docs
from backend.tools.issue_tracker_tool import check_issue_tracker

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOOL_ROUNDS = 5  # Safety cap on tool-call loops

# ------------------------------------------------------------------
# Tool definitions (OpenAI-compatible function-calling format)
# ------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
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
    },
]


# ------------------------------------------------------------------
# Tool dispatcher
# ------------------------------------------------------------------
def _execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    try:
        if name == "query_customer_db":
            result = query_customer_db(**arguments)
        elif name == "search_docs":
            result = search_docs(**arguments)
        elif name == "check_issue_tracker":
            result = check_issue_tracker(**arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
    except UnsafeQueryError as e:
        result = {"error": f"Query rejected: {e}"}
    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, default=str)


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def run_agent(
    user_message: str,
    conversation_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Run the agentic loop for a single user turn.

    Returns:
        {
            "answer": str,           # Final assistant response
            "tool_calls": list,      # Tool calls made during this turn
            "history": list,         # Full conversation history after this turn
        }
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    tool_calls_log: list[dict[str, Any]] = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]

        # If the model wants to call tools
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            # Append the assistant message (with tool_calls) to history
            messages.append(choice.message.model_dump())

            for tc in choice.message.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)

                result_str = _execute_tool(fn_name, fn_args)

                tool_calls_log.append({
                    "tool": fn_name,
                    "arguments": fn_args,
                    "result": json.loads(result_str),
                })

                # Append tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

            # Loop again — the model may want to call more tools
            continue

        # No more tool calls — the model produced a final answer
        answer = choice.message.content or ""
        messages.append({"role": "assistant", "content": answer})

        # Strip system prompt from returned history
        history = [m for m in messages if m.get("role") != "system"]

        return {
            "answer": answer,
            "tool_calls": tool_calls_log,
            "history": history,
        }

    # Safety: if we hit MAX_TOOL_ROUNDS, return what we have
    return {
        "answer": "I was unable to complete the request within the allowed number of tool calls.",
        "tool_calls": tool_calls_log,
        "history": [m for m in messages if m.get("role") != "system"],
    }
