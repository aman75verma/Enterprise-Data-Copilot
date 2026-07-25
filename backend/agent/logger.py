"""
Structured logger for tool invocations.

Logs every tool call with: tool name, arguments, result summary,
latency, execution path (direct / mcp), and timestamp.
"""

import json
import logging
import time
from contextlib import contextmanager
from typing import Any, Generator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("copilot")


@contextmanager
def log_tool_call(
    tool_name: str,
    arguments: dict[str, Any],
    path: str = "direct",
) -> Generator[dict[str, Any], None, None]:
    """
    Context manager that logs a tool invocation with timing.

    Usage:
        with log_tool_call("search_docs", {"query": "rls"}, path="direct") as ctx:
            ctx["result"] = search_docs(query="rls")
    """
    entry: dict[str, Any] = {
        "tool": tool_name,
        "path": path,
        "args": arguments,
        "result": None,
        "error": None,
        "latency_ms": 0,
    }
    start = time.perf_counter()
    try:
        yield entry
    except Exception as exc:
        entry["error"] = str(exc)
        raise
    finally:
        entry["latency_ms"] = round((time.perf_counter() - start) * 1000, 2)
        level = logging.ERROR if entry["error"] else logging.INFO
        # Keep log line compact: truncate large results
        summary = _summarize(entry)
        logger.log(level, summary)


def _summarize(entry: dict[str, Any]) -> str:
    result_preview = ""
    if entry["error"]:
        result_preview = f"ERROR: {entry['error'][:200]}"
    elif entry["result"] is not None:
        raw = json.dumps(entry["result"], default=str)
        result_preview = raw[:200] + ("..." if len(raw) > 200 else "")
    return (
        f"[{entry['path'].upper()}] {entry['tool']}  "
        f"args={json.dumps(entry['args'], default=str)[:150]}  "
        f"latency={entry['latency_ms']}ms  "
        f"result={result_preview}"
    )
