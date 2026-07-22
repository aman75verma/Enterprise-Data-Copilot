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
| 2 | Document RAG | pgvector — Supabase docs chunked + embedded | ⬜ Not started |
| 3 | External API | GitHub Issues REST API (`supabase/supabase`) | ⬜ Not started |

---

## MCP Tools

| Tool Name | Purpose | Status |
|---|---|---|
| `query_customer_db` | Read-only SQL against support DB | ⬜ Not started |
| `search_docs` | Semantic search over product docs | ⬜ Not started |
| `check_issue_tracker` | GitHub Issues lookup by keyword/number | ⬜ Not started |

---

## Chunk Progress Tracker

| Chunk | Description | Status | Date Completed | Notes |
|---|---|---|---|---|
| 0 | Domain Decision | ✅ Done (locked in spec) | Pre-project | Internal Support Copilot, Supabase reference |
| 1 | SQL Database + Seed Data | ✅ Done | 2026-07-21 | Postgres on port 5433 (avoided local conflict) |
| 2 | Document RAG Ingestion | ⬜ Not started | — | — |
| 3 | External API Tool | ⬜ Not started | — | — |
| 4 | MCP Tool Definitions | ⬜ Not started | — | — |
| 5 | Routing / Orchestrator | ⬜ Not started | — | — |
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
| — | Embedding model | Spec suggests `all-MiniLM-L6-v2` — *pending user confirmation* | — |
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
