"""
Conversation store — CRUD for conversations and turns.

Uses the shared DB pool for connection management.
"""

import json
import uuid
from typing import Any

import psycopg2.extras

from backend.db.pool import get_connection, put_connection


def create_conversation() -> str:
    """Create a new conversation and return its UUID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO conversations (id) VALUES (%s) RETURNING id",
                (str(uuid.uuid4()),),
            )
            conv_id = str(cur.fetchone()[0])
            conn.commit()
            return conv_id
    finally:
        put_connection(conn)


def save_turn(
    conversation_id: str,
    role: str,
    content: str,
    tool_calls: list[dict[str, Any]] | None = None,
    tool_name: str | None = None,
    latency_ms: int | None = None,
    token_usage: int | None = None,
) -> int:
    """Insert a single turn and return its ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO turns (conversation_id, role, content, tool_calls, tool_name, latency_ms, token_usage)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    conversation_id,
                    role,
                    content,
                    json.dumps(tool_calls, default=str) if tool_calls else None,
                    tool_name,
                    latency_ms,
                    token_usage,
                ),
            )
            turn_id = cur.fetchone()[0]
            conn.commit()
            return turn_id
    finally:
        put_connection(conn)


def get_conversation(conversation_id: str) -> dict[str, Any]:
    """Return a conversation with all its turns."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, created_at FROM conversations WHERE id = %s", (conversation_id,))
            conv = cur.fetchone()
            if not conv:
                return {"error": "Conversation not found"}

            cur.execute(
                "SELECT id, role, content, tool_calls, tool_name, latency_ms, created_at "
                "FROM turns WHERE conversation_id = %s ORDER BY created_at ASC",
                (conversation_id,),
            )
            turns = [dict(row) for row in cur.fetchall()]

            return {
                "conversation_id": str(conv["id"]),
                "created_at": str(conv["created_at"]),
                "turns": turns,
            }
    finally:
        put_connection(conn)


def get_recent_logs(limit: int = 50) -> list[dict[str, Any]]:
    """Return the most recent turns with tool calls (for admin dashboard)."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT t.id, t.conversation_id, t.role, t.content, t.tool_calls,
                       t.tool_name, t.latency_ms, t.created_at
                FROM turns t
                WHERE t.tool_calls IS NOT NULL
                ORDER BY t.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        put_connection(conn)
