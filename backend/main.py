"""
Enterprise Data Copilot — FastAPI Backend

Endpoints:
  POST /chat                   — Send a message, get an AI answer + tool trace
  GET  /conversations/{id}     — Retrieve full chat history
  GET  /admin/logs             — Recent turns with tool calls (dashboard)
  GET  /health                 — Liveness check
"""

import time
import os
from contextlib import asynccontextmanager
from typing import Any

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException 
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from backend.models import (
    ChatRequest,
    ChatResponse,
    CompareRequest,
    CompareResponse,
    ConversationResponse,
    HealthResponse,
    LogEntry,
    ToolCallEntry,
    TurnEntry,
)
from backend.agent.orchestrator import run_agent
from backend.db.conversation_store import (
    create_conversation,
    get_conversation,
    get_recent_logs,
    save_turn,
)
from backend.db.pool import close_pool

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    yield
    close_pool()


app = FastAPI(
    title="Enterprise Data Copilot",
    description="Internal Support Copilot API — powered by Groq + MCP tools",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend (Vite dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# POST /chat
# ------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message and receive an AI-generated answer with tool call trace."""
    # Resolve or create conversation
    conversation_id = req.conversation_id
    if not conversation_id:
        conversation_id = create_conversation()

    # Load prior turns as conversation history for the orchestrator
    history: list[dict[str, Any]] = []
    if req.conversation_id:
        conv = get_conversation(conversation_id)
        if "turns" in conv:
            for turn in conv["turns"]:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if role in ("user", "assistant"):
                    history.append({"role": role, "content": content})

    # Save the user turn
    save_turn(conversation_id, role="user", content=req.message)

    # Run the agent
    start = time.perf_counter()
    try:
        result = run_agent(user_message=req.message, conversation_history=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator error: {str(e)}")
    latency = round((time.perf_counter() - start) * 1000)

    # Determine primary tool used
    tool_name = result["tool_calls"][0]["tool"] if result["tool_calls"] else None

    # Save the assistant turn
    save_turn(
        conversation_id,
        role="assistant",
        content=result["answer"],
        tool_calls=result["tool_calls"],
        tool_name=tool_name,
        latency_ms=latency,
    )

    return ChatResponse(
        conversation_id=conversation_id,
        answer=result["answer"],
        tool_calls=[ToolCallEntry(**tc) for tc in result["tool_calls"]],
    )


# ------------------------------------------------------------------
# GET /conversations/{id}
# ------------------------------------------------------------------
@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(conversation_id: str):
    """Retrieve the full history of a conversation."""
    conv = get_conversation(conversation_id)
    if "error" in conv:
        raise HTTPException(status_code=404, detail=conv["error"])
    return ConversationResponse(
        conversation_id=conv["conversation_id"],
        created_at=conv["created_at"],
        turns=[TurnEntry(**{k: str(v) if k in ("created_at",) else v for k, v in t.items()}) for t in conv["turns"]],
    )


# ------------------------------------------------------------------
# GET /admin/logs
# ------------------------------------------------------------------
@app.get("/admin/logs", response_model=list[LogEntry])
async def admin_logs(limit: int = 50):
    """Return recent turns that include tool calls (for the admin dashboard)."""
    rows = get_recent_logs(limit=min(limit, 200))
    return [
        LogEntry(**{k: str(v) if k in ("created_at", "conversation_id") else v for k, v in row.items()})
        for row in rows
    ]


# ------------------------------------------------------------------
# POST /admin/compare
# ------------------------------------------------------------------
@app.post("/admin/compare", response_model=CompareResponse)
async def admin_compare(req: CompareRequest):
    """Run a tool via Direct path and return latencies."""
    from backend.agent.compare import _run_direct, _run_mcp_async
    import json

    try:
        result_a, ms_a = _run_direct(req.tool_name, req.arguments)
        
        mcp_ms = None
        mcp_error = None
        try:
            _, ms_b = await _run_mcp_async(req.tool_name, req.arguments)
            mcp_ms = round(ms_b, 2)
        except Exception as e:
            mcp_error = str(e)
        
        # Determine result preview string
        preview = ""
        if isinstance(result_a, list):
            preview = f"{len(result_a)} rows/items returned."
        elif isinstance(result_a, dict):
            if "rows" in result_a:
                preview = f"{len(result_a['rows'])} rows returned."
            elif "results" in result_a:
                preview = f"{len(result_a['results'])} items returned."
            else:
                preview = json.dumps(result_a)[:100]
        else:
            preview = str(result_a)[:100]
            
        return CompareResponse(
            tool_name=req.tool_name,
            direct_ms=round(ms_a, 2),
            mcp_ms=mcp_ms,
            mcp_error=mcp_error,
            result_preview=preview
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# GET /health
# ------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health():
    """Liveness check — verifies DB and embedding model are reachable."""
    from backend.db.pool import get_connection, put_connection

    db_status = "ok"
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        put_connection(conn)
    except Exception as e:
        db_status = f"error: {e}"

    emb_status = "ok"
    try:
        from backend.tools.docs_tool import get_embedding_model
        get_embedding_model()
    except Exception as e:
        emb_status = f"error: {e}"

    return HealthResponse(status="ok", database=db_status, embedding_model=emb_status)
