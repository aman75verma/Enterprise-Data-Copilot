# Project 1: Enterprise Data Copilot
### (RAG + MCP Tool Routing + Multi-Source Q&A)

## 1. What This Project Is

A chat assistant that answers questions across **three different types of data sources**:
1. A **SQL database** (structured data — e.g. orders, users, employees, whatever domain you pick)
2. A pile of **unstructured documents** (PDFs, docs — company policies, reports, manuals)
3. A **live external API** (e.g. GitHub, weather, a public dataset)

Instead of dumping everything into one vector store (the "basic RAG" mistake), the agent **decides which tool to call** for each question — SQL query, document search, or API call — using MCP (Model Context Protocol) as the tool-exposure layer. This mirrors real Forward Deployed Engineering work: wiring a client's messy, heterogeneous systems into one usable interface.

**Why it stands out:** Most portfolio RAG projects are "upload a PDF, ask questions about it." Multi-source routing + agentic tool selection shows you understand orchestration, not just embeddings.

---

## 2. High-Level Architecture

```
                        ┌─────────────────────┐
                        │   React Frontend     │
                        │  (chat UI, streaming) │
                        └──────────┬───────────┘
                                   │ HTTP/SSE
                        ┌──────────▼───────────┐
                        │   FastAPI Backend     │
                        │  - auth/session        │
                        │  - agent orchestrator  │
                        └──────────┬───────────┘
                                   │
                     ┌─────────────┼─────────────┐
                     │             │             │
              ┌──────▼─────┐ ┌────▼─────┐ ┌─────▼──────┐
              │ MCP Server │ │MCP Server│ │ MCP Server │
              │  SQL Tool  │ │ Doc RAG  │ │ External   │
              │ (NL→SQL)   │ │ (vector) │ │ API Tool   │
              └──────┬─────┘ └────┬─────┘ └─────┬──────┘
                     │             │             │
              ┌──────▼─────┐ ┌────▼─────┐ ┌─────▼──────┐
              │  Postgres  │ │ pgvector │ │  3rd Party │
              │  (app data)│ │ /Chroma  │ │    API     │
              └────────────┘ └──────────┘ └────────────┘
```

Everything runs in Docker containers, deployed via a CI/CD pipeline.

---

## 3. Detailed Request Flow (what happens when a user asks a question)

1. User types a question in the React chat UI → sent via POST/SSE to FastAPI backend.
2. Backend loads conversation history + creates a new turn.
3. **Orchestrator LLM call #1 (routing):** the LLM is given the user's question + a list of available MCP tools (with descriptions) and decides which tool(s) to call. This is the core "agent" behavior — not a hardcoded if/else.
4. Depending on routing decision:
   - **SQL path:** LLM generates a SQL query (or calls a constrained NL→SQL tool) → query runs against Postgres → rows returned.
   - **Document path:** question is embedded → similarity search against pgvector/Chroma → top-k chunks retrieved.
   - **API path:** LLM calls the external API tool with structured parameters → JSON response returned.
5. Tool result(s) are fed back into a **second LLM call** that synthesizes a natural-language answer, citing which source it used.
6. Answer streams back to the frontend token-by-token (SSE/websocket).
7. Full turn (question, tool calls, answer) is logged to Postgres for the evals/observability dashboard.

---

## 4. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Tailwind | Standard, in-demand, fast to build |
| Streaming | Server-Sent Events (SSE) | Simpler than websockets for one-way token streaming |
| Backend | FastAPI (Python) | Async-native, pairs well with LLM SDKs |
| Agent/LLM | **Groq API (Llama 3.3 70B)** — free tier, fast, solid tool-calling. Fallback: **Ollama** (local, e.g. `llama3.1:8b` or `qwen2.5:7b`) for fully offline dev | No paid API key needed. Groq gives you a stronger model for free; Ollama gives you zero-cost/offline but weaker tool-calling accuracy |
| Embeddings | **sentence-transformers** (local, e.g. `all-MiniLM-L6-v2` or `bge-small-en`) | Free, runs on CPU, no API call needed — keeps the RAG pipeline working even if your LLM API is down |
| Tool protocol | MCP (Model Context Protocol) | Industry-emerging standard, strong resume signal — model-agnostic, works the same regardless of which LLM provider you use |
| Structured data | PostgreSQL | Universal, SQL is a hard requirement for SDE roles |
| Vector store | pgvector (extension on same Postgres) or Chroma | pgvector = one less service to run; Chroma = simpler API |
| Auth | JWT-based session auth | Basic but real auth flow |
| Containerization | Docker + docker-compose | Multi-service local dev |
| CI/CD | GitHub Actions | Lint → test → build → push image → deploy |
| Deployment | Fly.io / Render / Railway | Free/cheap tiers, simple Docker deploy |
| Observability | Simple logging table + a `/admin` dashboard page | Shows product thinking, not just a demo |

---

## 5. Prerequisites — What to Learn Before/While Building

Don't try to learn everything first — learn just enough to start, then go deeper as you hit walls. Suggested order:

**Must know before starting:**
- Python basics + REST API concepts (what is a request/response, status codes, JSON)
- SQL fundamentals: SELECT/JOIN/WHERE/GROUP BY, and how a DB schema is designed (normalization basics)
- What embeddings are and how vector similarity search works (conceptually — cosine similarity, top-k retrieval)
- What "function calling" / "tool use" means for an LLM (the model doesn't run code — it emits structured intent, your backend executes it)
- Git basics (branches, commits, PRs) — you'll need this for CI/CD anyway

**Learn while building (just-in-time):**
- FastAPI basics (routes, async, pydantic models) — a few hours of tutorial is enough to start
- React basics if you don't know it (components, state, effects) — or reuse a chat UI template and focus energy elsewhere
- Docker basics: what an image vs container is, writing a Dockerfile, docker-compose for multi-service
- What MCP actually is (read Anthropic's MCP docs — it's a protocol for exposing tools/resources to LLMs over a standard interface)
- GitHub Actions YAML basics (jobs, steps, triggers)
- **No paid API needed:** sign up for a free Groq API key (groq.com) for the chat/tool-calling model, and use `sentence-transformers` locally for embeddings — this whole project can be built at zero cost. If you want a fully offline fallback, install Ollama and pull `llama3.1:8b` or `qwen2.5:7b`, both of which support tool calling.

**Nice to have (deepen after MVP works):**
- Prompt engineering for tool-routing accuracy (few-shot examples of good tool selection) — matters more with free/smaller models, since routing mistakes are more common than with frontier models
- Basic evals: how do you measure if the agent picked the right tool?
- Rate limiting / cost control — even on free tiers, Groq enforces requests-per-minute limits, so build in basic retry/backoff logic

---

## 6. Your Assignments (What YOU Must Personally Do)

You said you'll use AI agents to build this but want to actually understand it. Here's the split that keeps you honest — **you own the decisions and the debugging, the AI accelerates the typing.**

### Phase 0 — Design (100% you, no AI)
- [ ] Pick your domain (e.g. "internal HR assistant", "e-commerce support bot", "personal finance copilot"). A concrete domain makes the SQL schema and documents meaningful.
- [ ] Sketch your own DB schema on paper (3-5 tables) before asking AI to generate anything. You must be able to explain every foreign key in an interview.
- [ ] Write down, in your own words, what "routing" means and why it's better than naive RAG. If you can't explain this without notes, you don't own the project yet.

### Phase 1 — Scaffolding (AI-assisted, you review every file)
- [ ] Ask the agent to scaffold FastAPI backend + React frontend + Docker setup — but **read every generated file line by line** and ask the agent to explain any line you don't understand.
- [ ] Set up Postgres schema yourself (even if AI writes the SQL, you type/run the migration and verify the tables exist via `psql` or a GUI).

### Phase 2 — Core Logic (you drive, AI assists)
- [ ] Implement the routing logic yourself first as a rough version (even simple keyword-based routing) so you understand the *problem* before letting AI build the elegant version.
- [ ] Wire up ONE MCP tool (say, the SQL tool) fully by hand, tracing a request from frontend click → backend → SQL execution → response, in a debugger or with print statements. Do this before wiring the other two tools with AI help.
- [ ] Write 10-15 test questions yourself (mix of SQL-answerable, doc-answerable, API-answerable, and ambiguous ones) — this becomes your eval set and your demo script.

### Phase 3 — Polish & Infra (AI-assisted, you configure)
- [ ] Write the Dockerfile yourself for at least one service; let AI help with the rest once you understand the pattern.
- [ ] Set up the GitHub Actions pipeline yourself, one job at a time (lint → test → build), testing each stage before adding the next.
- [ ] Deploy it yourself and fix at least one real deployment failure without asking AI to just "fix it" — read the actual error log first.

### Phase 4 — Interview-Proofing
- [ ] Write a 1-page README explaining architecture decisions and trade-offs (why Postgres+pgvector over separate vector DB, why SSE over websockets, etc.)
- [ ] Prepare answers to: "What happens if the LLM picks the wrong tool?", "How would you scale this to 10,000 documents?", "How do you prevent SQL injection if the LLM generates SQL?"
- [ ] Record a 2-minute demo video/GIF for your resume/portfolio site.

---

## 7. Suggested Build Order (2–3 week pace)

| Week | Milestone |
|---|---|
| 1 | Schema design + Postgres running in Docker + basic FastAPI CRUD endpoints working |
| 1–2 | Frontend chat shell + one working end-to-end path (SQL tool only, no routing yet) |
| 2 | Add document RAG tool + external API tool + routing logic |
| 2–3 | Streaming responses, logging/eval table, polish UI |
| 3 | Dockerize fully, CI/CD pipeline, deploy, write README, record demo |

---

## 8. Stretch Goals (if you have extra time)
- Multi-tenancy (different users see different data)
- A simple admin dashboard showing tool-call accuracy over your eval set
- Caching layer (Redis) for repeated queries
- Swap in a second LLM provider to compare routing accuracy
