# Project 1 — Implementation Blueprint
### Everything is decided. Nothing left but building it.

This document locks in every design decision for the Enterprise Data Copilot so that **any model (even a weaker/free one) can implement it chunk-by-chunk without making judgment calls.** Feed one chunk at a time to your coding agent. Each chunk is self-contained and has a "definition of done."

---

## CHUNK 0 — Domain (Locked)

**Domain: Internal Support Copilot** for a SaaS product.

We're using **Supabase** (an open-source backend-as-a-service company) as the reference product, because it gives us three *real, free, legally usable* data sources instead of fake placeholder data:

| Source | What it is | Where it comes from |
|---|---|---|
| SQL DB | Synthetic customer/subscription/ticket/invoice data | You generate it (script provided below) |
| Documents | Real product documentation | Cloned from Supabase's public GitHub docs |
| External API | Real, live issue tracker | GitHub Issues API on `supabase/supabase` |

**The product framing (use this in your README/demo):** "An internal tool support agents use to answer customer questions by pulling account/billing info from the DB, product knowledge from the docs, and live bug/issue status from GitHub."

This is now fixed. Do not re-decide this while building — if you get the urge to change domain mid-build, that's scope creep, not progress.

---

## CHUNK 1 — SQL Database (Locked)

### 1.1 Schema — run this exact SQL to create your tables

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    country TEXT,
    timezone TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    billing_email TEXT NOT NULL,
    owner_customer_id INTEGER NOT NULL REFERENCES customers(id),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    project_ref TEXT UNIQUE NOT NULL,
    project_name TEXT NOT NULL,
    region TEXT NOT NULL,
    postgres_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'paused', 'suspended', 'restoring', 'coming_up')),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE usage_metrics (
    project_id INTEGER PRIMARY KEY REFERENCES projects(id),
    database_size_gb NUMERIC(10,2) NOT NULL DEFAULT 0,
    storage_gb NUMERIC(10,2) NOT NULL DEFAULT 0,
    bandwidth_gb NUMERIC(10,2) NOT NULL DEFAULT 0,
    api_requests BIGINT NOT NULL DEFAULT 0,
    active_users INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    plan TEXT NOT NULL CHECK (plan IN ('free', 'pro', 'team', 'enterprise')),
    status TEXT NOT NULL CHECK (status IN ('active', 'past_due', 'cancelled', 'trialing')),
    monthly_cost NUMERIC(10,2) NOT NULL,
    renewal_date DATE,
    started_at DATE NOT NULL
);

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    invoice_number TEXT UNIQUE NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    tax NUMERIC(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending', 'failed', 'refunded')),
    payment_method TEXT,
    billing_period TEXT NOT NULL,
    due_date DATE NOT NULL,
    paid_at TIMESTAMP
);

CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    project_id INTEGER REFERENCES projects(id),
    agent_id INTEGER REFERENCES agents(id),
    subject TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('billing', 'technical', 'account', 'feature_request', 'bug')),
    affected_product TEXT CHECK (affected_product IN ('Auth', 'Database', 'Storage', 'Edge Functions', 'Realtime', 'Dashboard', 'Billing', 'CLI', 'Other')),
    status TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'urgent')),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    resolved_at TIMESTAMP
);

CREATE TABLE ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    sender_type TEXT NOT NULL CHECK (sender_type IN ('customer', 'agent')),
    message TEXT NOT NULL,
    internal_note BOOLEAN NOT NULL DEFAULT false,
    attachments JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
```

### 1.2 Seed data — generation plan

Write a Python script `seed.py` using the `faker` library that builds a coherent story:
- Generate Customers, Organizations, and Projects hierarchically.
- Generate realistic Usage Metrics (active vs paused).
- Base Subscriptions and Invoices on usage.
- Generate Support Tickets logically tied to the state (e.g. quota warnings for high storage, suspension tickets for past_due invoices).
- Use Supabase-specific subjects like "Row Level Security policy not working".

**Definition of done:** running `python seed.py` populates all tables hierarchically, and tickets match the project states.

### 1.3 Sample questions this table should answer (your eval set for the SQL tool)
1. "What's the status of the subscription for organization [org_name]?"
2. "How many open tickets does project [project_ref] have?"
3. "List all projects on Postgres 14 that have active users."
4. "What was [org_name]'s last invoice amount and was it paid?"
5. "Which agent has resolved the most 'Storage' tickets this month?"

---

## CHUNK 2 — Documents / RAG Corpus (Locked)

### 2.1 Source
Clone Supabase's public documentation repository:
```bash
git clone --depth 1 https://github.com/supabase/supabase.git
```
Look inside for the docs content folder — in Supabase's monorepo this lives under a path like `apps/docs/content` (repo structures shift over time, so if that exact path is wrong, search the cloned repo for a folder containing many `.mdx` or `.md` files — that's your target). Collect all `.md`/`.mdx` files under that docs folder.

**Fallback if the path/structure has changed or cloning is inconvenient:** use any of these instead — same approach, same license type (open-source docs repos):
- `github.com/PostHog/posthog.com` (docs are in `contents/docs`)
- `github.com/appwrite/docs`

Pick ONE. Don't mix multiple products' docs — it should feel like one coherent knowledge base.

### 2.2 Ingestion pipeline steps
1. Walk the docs folder, read every `.md`/`.mdx` file.
2. Strip frontmatter (YAML metadata at the top of each file) and any MDX component syntax — keep plain markdown/text.
3. Chunk each document: ~500 tokens per chunk, ~50 token overlap between chunks (use `langchain`'s `RecursiveCharacterTextSplitter` or write your own simple splitter — either is fine, but you must understand what it's doing).
4. For each chunk, generate an embedding using `sentence-transformers` (`all-MiniLM-L6-v2`).
5. Store in Postgres via `pgvector`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE doc_chunks (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- 384 = all-MiniLM-L6-v2 output dimension
    title TEXT,
    product TEXT,
    section TEXT,
    url TEXT,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMP NOT NULL DEFAULT now()
);
```
6. At query time: embed the user's question with the same model, run:
```sql
SELECT content, source_file
FROM doc_chunks
ORDER BY embedding <-> $1
LIMIT 5;
```

**Definition of done:** `SELECT count(*) FROM doc_chunks;` returns a few hundred to a few thousand rows (depends on doc volume), and a manual test query like "how do I set up row level security" returns relevant chunks.

### 2.3 Sample questions this should answer (your eval set for the doc tool)
1. "How do I enable row level security on a table?"
2. "What's the difference between the free and pro plan?" (if covered in docs — if not, this becomes a good test of "the agent should say it doesn't know")
3. "How do I set up authentication with email/password?"
4. "What are storage buckets and how do I use them?"
5. "How do I write a database function?"

---

## CHUNK 3 — Third-Party API (Locked)

### 3.1 API: GitHub REST API — Issues endpoint

No signup/API key strictly required for public read access (rate-limited to 60 requests/hour unauthenticated). For higher limits, generate a free GitHub Personal Access Token (5,000 requests/hour) and pass it as a header — recommended so you don't hit limits while testing.

**Base endpoint:**
```
GET https://api.github.com/repos/supabase/supabase/issues?state=open&per_page=10
```

**Auth header (optional but recommended):**
```
Authorization: Bearer YOUR_GITHUB_PAT
```

**Example: fetch a specific issue**
```
GET https://api.github.com/repos/supabase/supabase/issues/{issue_number}
```

**Example: search issues by keyword**
```
GET https://api.github.com/search/issues?q=repo:supabase/supabase+is:issue+RLS+in:title
```

### 3.2 What this tool represents in the product
Frame this as: "check if a customer's bug report matches a known/open issue." In your tool description (for the LLM), phrase it as querying "the live issue tracker," not "GitHub" — keeps the product framing consistent even though under the hood it's really GitHub Issues.

### 3.3 Sample questions this should answer (your eval set for the API tool)
1. "Is there an open issue about [some bug topic, e.g. connection timeouts]?"
2. "What's the status of issue #[number]?"
3. "How many open bugs are labeled as high priority?" (if labels are used — check what labels exist on real issues first)

---

## CHUNK 4 — MCP Tool Definitions (Locked)

Implement exactly these three MCP tools. Use this as your spec — implement the server, don't redesign the interface.

### Tool 1: `query_customer_db`
```json
{
  "name": "query_customer_db",
  "description": "Run a read-only SQL query against the customer support database (customers, organizations, projects, usage_metrics, subscriptions, invoices, tickets, ticket_messages, agents tables). Use for questions about a specific customer, project, organization, billing, or ticket history.",
  "input_schema": {
    "type": "object",
    "properties": {
      "sql_query": { "type": "string", "description": "A read-only SELECT query" }
    },
    "required": ["sql_query"]
  }
}
```
**Safety requirement:** backend must reject any query that isn't a `SELECT` (block INSERT/UPDATE/DELETE/DROP) before execution. This is a real interview talking point — mention it explicitly in your README.

### Tool 2: `search_docs`
```json
{
  "name": "search_docs",
  "description": "Search product documentation for how-to guides, feature explanations, and setup instructions. Use for general product knowledge questions not tied to a specific customer's account.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "The search query" },
      "top_k": { "type": "integer", "description": "Number of chunks to return", "default": 5 }
    },
    "required": ["query"]
  }
}
```

### Tool 3: `check_issue_tracker`
```json
{
  "name": "check_issue_tracker",
  "description": "Check the live issue tracker for open bugs or feature requests matching a keyword, or look up a specific issue by number. Use when a customer reports a bug and you need to check if it's a known issue.",
  "input_schema": {
    "type": "object",
    "properties": {
      "keyword": { "type": "string", "description": "Search keyword, omit if using issue_number" },
      "issue_number": { "type": "integer", "description": "Specific issue number to look up, omit if searching by keyword" }
    }
  }
}
```

---

## CHUNK 5 — Routing / Orchestration Logic (Locked)

### 5.1 System prompt template (use as-is, refine wording only)

```
You are an internal support copilot. You have access to three tools:
- query_customer_db: for account, billing, subscription, ticket questions about a specific customer
- search_docs: for general "how do I..." product knowledge questions
- check_issue_tracker: for checking if a reported bug is a known issue

Given the user's question:
1. Decide which tool(s) you need — you may call more than one if the question spans categories.
2. Call the tool(s).
3. Once you have results, write a clear answer citing which source(s) you used.
4. If no tool result answers the question, say so honestly — do not guess.
```

### 5.2 Few-shot routing examples (include these in your prompt or as test cases)

| Question | Correct tool |
|---|---|
| "What plan is jane@acme.com on?" | `query_customer_db` |
| "How do I enable RLS?" | `search_docs` |
| "Is there a known issue with connection pooling timeouts?" | `check_issue_tracker` |
| "jane@acme.com says storage isn't working — is this a known bug, and what's her plan?" | BOTH `query_customer_db` AND `check_issue_tracker` |

That last row is your hardest test case — a question needing two tools. Make sure your agent loop supports multiple sequential tool calls, not just one.

---

## CHUNK 6 — Backend Structure (Locked)

```
backend/
  main.py                 # FastAPI app, routes
  agent/
    orchestrator.py        # the routing + tool-calling loop
    system_prompt.py        # the prompt from Chunk 5
  tools/
    sql_tool.py             # implements query_customer_db (with SELECT-only guard)
    docs_tool.py             # implements search_docs
    issue_tracker_tool.py    # implements check_issue_tracker
  db/
    schema.sql               # Chunk 1 SQL
    seed.py                    # Chunk 1 seed script
    ingest_docs.py               # Chunk 2 ingestion script
  models.py                # pydantic request/response models
  requirements.txt
  Dockerfile
```

**Required endpoints:**
- `POST /chat` — accepts `{message, conversation_id}`, returns streamed response (SSE)
- `GET /conversations/{id}` — returns chat history
- `GET /admin/logs` — returns recent turns with tool calls made (for your dashboard)

---

## CHUNK 7 — Frontend Structure (Locked)

```
frontend/
  src/
    components/
      ChatWindow.tsx
      MessageBubble.tsx
      ToolCallTrace.tsx    # shows which tool(s) were called, expandable
    pages/
      Chat.tsx
      AdminDashboard.tsx    # shows logged turns + tool accuracy against your eval set
    api/
      client.ts             # fetch/SSE wrapper for backend calls
  package.json
  Dockerfile
```

---

## CHUNK 8 — Infra (Locked)

`docker-compose.yml` services:
1. `postgres` (with pgvector extension enabled)
2. `backend` (FastAPI, depends_on postgres)
3. `frontend` (React, depends_on backend)

GitHub Actions pipeline (`.github/workflows/ci.yml`) stages:
1. `lint` — run `ruff`/`eslint`
2. `test` — run backend unit tests (mock the LLM calls, test the SELECT-only SQL guard and the doc chunking logic)
3. `build` — build Docker images
4. `deploy` — push to Fly.io/Render on merge to `main`

---

## CHUNK 9 — Full Eval Set (Locked)

Combine all eval questions from Chunks 1-3 into one file `eval_questions.json`, each entry shaped as:
```json
{ "question": "What plan is jane@acme.com on?", "expected_tool": "query_customer_db" }
```
Write a script `run_eval.py` that sends each question through the agent and checks whether the expected tool was called. Report accuracy %. This becomes both your test suite and a genuine portfolio artifact ("my agent hits X% correct tool selection on a 15-question eval set").

---

## CHUNK 10 — Implementation Order (Locked)

Give your coding agent one chunk at a time, in this order, and verify "definition of done" before moving to the next:

1. Chunk 1 (SQL DB + seed data) → verify data exists
2. Chunk 2 (Docs ingestion) → verify chunks exist and a manual similarity query works
3. Chunk 3 (API tool) → verify a raw call to GitHub API returns issues
4. Chunk 4 (wrap all three as MCP tools) → verify each tool works in isolation via a test script
5. Chunk 5 (orchestrator + system prompt) → verify single-tool routing works on 5 questions
6. Chunk 6 (backend endpoints) → verify `/chat` works via curl/Postman
7. Chunk 9 (eval set) → run it, get a baseline accuracy number
8. Chunk 7 (frontend) → connect to backend, verify chat works in browser
9. Chunk 8 (Docker + CI/CD) → containerize, then automate

**Stop building new features once all 10 chunks are done.** Polish, write the README, record the demo. Scope creep past this point hurts you more than it helps.
