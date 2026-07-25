# Enterprise Data Copilot — AI Development Log

> **Purpose**: This document tracks ALL work done on this project — configurations, decisions, completed chunks, environment setup, and issues encountered. Any future AI agent should read this file FIRST to understand the project state and resume work.

---

## Project Metadata

| Key | Value |
|---|---|
| **Project Name** | Enterprise Data Copilot |
| **Domain** | Internal Support Copilot for SaaS (Supabase reference) |
| **Workspace** | `c:\Users\ammua\Desktop\Enterprise Data Copilot` |
| **Started** | 2026-07-21 |
| **Spec Files** | `Enterprise Data Copilot.md`, `Project Chunks.md` |
| **Implementation Plan** | See `implementation_plan.md` artifact |
| **Build Approach** | Chunk-by-chunk, user-reviewed after each chunk |

---

## Architecture Summary

- **Frontend**: React + TypeScript + Tailwind (Vite bundler)
- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16 + pgvector extension
- **LLM**: Groq API (Llama 3.3 70B) — *pending user confirmation*
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU)
- **Tool Protocol**: MCP (Model Context Protocol)
- **Streaming**: Server-Sent Events (SSE)
- **Auth**: JWT-based session auth
- **Infra**: Docker + docker-compose, GitHub Actions CI/CD

---

## Data Sources

| # | Source | Implementation | Status |
|---|---|---|---|
| 1 | SQL Database | Postgres — customers, subscriptions, invoices, agents, tickets, ticket_messages | ✅ Done |
| 2 | Document RAG | pgvector - Supabase docs chunked + embedded in `doc_chunks` | Done |
| 3 | External API | GitHub Issues REST API (`supabase/supabase`) via live issue tracker client | Done |

---

## MCP Tools

| Tool Name | Purpose | Status |
|---|---|---|
| `query_customer_db` | Read-only SQL against support DB; rejects non-SELECT/write/admin queries | Done |
| `search_docs` | Semantic search over product docs in `doc_chunks` | Done |
| `check_issue_tracker` | Live issue tracker lookup by keyword/number | Done |

---

## Chunk Progress Tracker

| Chunk | Description | Status | Date Completed | Notes |
|---|---|---|---|---|
| 0 | Domain Decision | ✅ Done (locked in spec) | Pre-project | Internal Support Copilot, Supabase reference |
| 1 | SQL Database + Seed Data | ✅ Done | 2026-07-21 | Postgres on port 5433 (avoided local conflict) |
| 2 | Document RAG Ingestion | Done | 2026-07-22 | Ingested 6,833 chunks from Supabase docs into `doc_chunks` |
| 3 | External API Tool | Done | 2026-07-22 | Added live issue tracker client for search, issue lookup, labels, and label counts |
| 4 | MCP Tool Definitions | Done | 2026-07-23 | Added real MCP server exposing `query_customer_db`, `search_docs`, and `check_issue_tracker` |
| 5 | Routing / Orchestrator | Done | 2026-07-23 | Groq Llama 3.3 70B, multi-tool loop, system prompt |
| 5.1 | Standardization Pass | Done | 2026-07-25 | Tool registry, structured logging, DB pool, error types, comparison runner |
| 6 | Backend Endpoints | ⬜ Not started | — | — |
| 7 | Frontend | ⬜ Not started | — | — |
| 8 | Infrastructure (Docker/CI) | ⬜ Not started | — | — |
| 9 | Eval Set | ⬜ Not started | — | — |

---

## Environment & Configuration

### Required Software
- [ ] Python 3.11+
- [ ] Node.js 20+
- [ ] Docker Desktop
- [ ] Git

### API Keys & Secrets (to be configured in `.env`)
- [ ] `DATABASE_URL` — Postgres connection string
- [ ] `GROQ_API_KEY` — Groq API key for LLM (free tier)
- [ ] `GITHUB_TOKEN` — GitHub PAT for higher rate limits (optional)

### Ports
| Service | Port |
|---|---|
| Postgres | 5432 |
| Backend (FastAPI) | 8000 |
| Frontend (Vite dev) | 5173 |

---

## Decision Log

| Date | Decision | Rationale | Decided By |
|---|---|---|---|
| 2026-07-21 | Project kickoff — plan created | Following chunk-by-chunk blueprint | AI + User |
| — | LLM provider | *Pending user input* | — |
| 2026-07-22 | Embedding model | Using `sentence-transformers/all-MiniLM-L6-v2` per Chunk 2 spec | AI + User |
| 2026-07-23 | MCP implementation | Built a real Python MCP server with `mcp.server.fastmcp.FastMCP`, plus a CLI demo runner for local testing | AI + User |
| — | Frontend bundler | Recommending Vite — *pending user confirmation* | — |

---

## Changelog

### 2026-07-21 — Session 1: Project Initialization
- **Read**: Both spec files (`Enterprise Data Copilot.md`, `Project Chunks.md`)
- **Created**: Implementation plan artifact (`implementation_plan.md`)
- **Created**: This AI development log (`ai_dev_log.md`)
- **Status**: Awaiting user approval on implementation plan before starting Chunk 1
- **Open Questions**:
  1. LLM provider preference (Groq / OpenAI / Ollama)?
  2. Do you have Docker Desktop installed?
  3. GitHub PAT available?
  4. OK with `all-MiniLM-L6-v2` for embeddings?
  5. Vite as React bundler?

### 2026-07-22 — Database Layer Redesign (SaaS/BaaS Model)
- **Architectural Change**: Remodeled the database schema to reflect a Supabase-like BaaS platform.
- **Added Entities**: `organizations`, `projects`, `usage_metrics`.
- **Refactored Entities**: Moved `subscriptions` and `invoices` to organizations. Added `project_id` and `affected_product` to tickets.
- **Seed Script**: Rewrote `seed.py` completely to generate story-driven, coherent data (e.g., quota warnings for high storage).
- **Documentation**: Updated `Enterprise Data Copilot.md` and `Project Chunks.md` to match new specifications. Created `docs/data_architecture.md`.

### 2026-07-25 — Standardization Pass (Dual-Path Quality)
- **Fixed**: Typo in `issue_tracker_tool.py` (`LiveIlssueTrackerClient` -> `LiveIssueTrackerClient`).
- **Created**: `backend/tools/tool_registry.py` — single source of truth for all tool schemas.
- **Created**: `backend/tools/errors.py` — standardized `ToolError` base class.
- **Created**: `backend/agent/logger.py` — structured logging with latency tracking.
- **Created**: `backend/db/pool.py` — threaded DB connection pool.
- **Created**: `backend/agent/compare.py` — dual-path comparison runner.
- **Refactored**: `orchestrator.py` now imports tool schemas from registry + uses logger.
- **Refactored**: `mcp_server.py` now imports descriptions from registry + uses logger.

### 2026-07-23 — Chunk 5: Routing / Orchestrator
- **Created**: `backend/agent/system_prompt.py` with the Chunk 5 system prompt (extended with schema context).
- **Created**: `backend/agent/orchestrator.py` with a full agentic tool-calling loop using Groq SDK.
- Supports multi-tool sequential calls (up to 5 rounds), conversation history, and structured tool result injection.
- Installed `groq` SDK.

### 2026-07-23 — Chunk 0-4 Handoff Guide
- **Created**: `docs/chunk0-4_handoff.md` as a compact walkthrough of Chunks 0 through 4.
- **Purpose**: Summarizes what is synthetic vs live, maps the key backend/tool files, and lists the study topics needed before Chunk 5.

---

## File Structure (Planned)

```
Enterprise Data Copilot/
├── docker-compose.yml
├── .env
├── .env.example
├── ai_dev_log.md              ← THIS FILE
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── agent/
│   │   ├── orchestrator.py
│   │   └── system_prompt.py
│   ├── tools/
│   │   ├── sql_tool.py
│   │   ├── docs_tool.py
│   │   └── issue_tracker_tool.py
│   ├── db/
│   │   ├── schema.sql
│   │   ├── seed.py
│   │   ├── ingest_docs.py
│   │   └── conversation_store.py
│   ├── eval/
│   │   ├── eval_questions.json
│   │   └── run_eval.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ToolCallTrace.tsx
│   │   ├── pages/
│   │   │   ├── Chat.tsx
│   │   │   └── AdminDashboard.tsx
│   │   └── api/
│   │       └── client.ts
│   ├── package.json
│   └── Dockerfile
└── .github/
    └── workflows/
        └── ci.yml
```

---

## Notes for Future AI Agents

1. **Always read this file first** before making changes
2. **Check the Chunk Progress Tracker** to know where work left off
3. **Follow the implementation order** from Chunk 10 in `Project Chunks.md`
4. **Verify "Definition of Done"** for each chunk before marking complete
5. **Update this log** after every work session with what was done
6. **The spec files are the source of truth** — don't deviate from locked decisions
