"""Standardized error types for all Copilot tools."""


class ToolError(Exception):
    """Base error for any tool failure. Both orchestrator and MCP server catch this."""

    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        self.message = message
        super().__init__(f"[{tool_name}] {message}")
