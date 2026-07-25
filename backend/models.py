"""Pydantic request/response models for the FastAPI endpoints."""

from pydantic import BaseModel, Field
from typing import Any


# --- Request models ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user's question")
    conversation_id: str | None = Field(None, description="Existing conversation UUID (omit to start new)")


# --- Response models ---

class ToolCallEntry(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result: dict[str, Any] | list[Any]


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    tool_calls: list[ToolCallEntry] = []


class TurnEntry(BaseModel):
    id: int
    role: str
    content: str
    tool_calls: Any | None = None
    tool_name: str | None = None
    latency_ms: int | None = None
    created_at: str | None = None


class ConversationResponse(BaseModel):
    conversation_id: str
    created_at: str
    turns: list[TurnEntry] = []


class LogEntry(BaseModel):
    id: int
    conversation_id: str
    role: str
    content: str
    tool_calls: Any | None = None
    tool_name: str | None = None
    latency_ms: int | None = None
    created_at: str | None = None


class HealthResponse(BaseModel):
    status: str
    database: str
    embedding_model: str
