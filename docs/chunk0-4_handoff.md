# Enterprise Data Copilot: Chunk 0 to Chunk 4 Handoff

This is the short version of the project so far. Read this if you want to understand what is real, what is synthetic, where the code lives, and what you need to learn before starting Chunk 5.

## What We Built

The product is an internal support copilot for a Supabase-like SaaS.

The system answers three kinds of questions:

- account, billing, subscription, and ticket questions from Postgres
- product knowledge questions from Supabase documentation
- bug/issue questions from the live public issue tracker

The important design point is that not all data is the same kind of real.

- The support database is synthetic, but it is structured to look realistic.
- The docs corpus is real Supabase documentation, ingested into vector search.
- The issue tracker is real and live, pulled from GitHub Issues for `supabase/supabase`.

That means the app can still work even though the customer database is fake, because each tool answers a different class of question.

## Chunk Story

### Chunk 0: Domain decision

We locked the product scope to internal support for a SaaS company, using Supabase as the reference model.

This matters because it gives the copilot three believable data sources instead of a generic chatbot setup.

### Chunk 1: SQL database

We created the support schema in Postgres and seeded it with hierarchical business data.

Core tables:

- `customers`
- `organizations`
- `projects`
- `usage_metrics`
- `subscriptions`
- `invoices`
- `agents`
- `tickets`
- `ticket_messages`

The seed data is synthetic, but it is meant to behave like real support data. That is why ticket patterns follow project state, invoice state, and usage state.

### Chunk 2: Document RAG

We ingested Supabase docs into `doc_chunks` using embeddings.

Core idea:

- split docs into chunks
- embed each chunk with `sentence-transformers/all-MiniLM-L6-v2`
- store the vectors in Postgres with `pgvector`
- search by similarity when the user asks a how-to question

This gives the assistant product knowledge without hardcoding answers.

### Chunk 3: External API tool

We added a live issue tracker client on top of GitHub Issues.

This tool lets the system search open issues or fetch a specific issue number.

The purpose is to answer questions like:

- is this a known bug?
- is there already an open issue?
- what is the current state of issue #1234?

### Chunk 4: MCP tool definitions

We wrapped the three data sources as real MCP tools.

Tools now exposed by the server:

- `query_customer_db`
- `search_docs`
- `check_issue_tracker`

The key safety rule is in `query_customer_db`: it rejects anything except read-only `SELECT` queries before execution.

## Main Files

If you want to follow the code, start here:

- [backend/tools/sql_tool.py](../backend/tools/sql_tool.py) - safe read-only SQL access to Postgres
- [backend/tools/docs_tool.py](../backend/tools/docs_tool.py) - embedding search over `doc_chunks`
- [backend/tools/issue_tracker_tool.py](../backend/tools/issue_tracker_tool.py) - live issue tracker wrapper
- [backend/tools/mcp_server.py](../backend/tools/mcp_server.py) - MCP server that exposes the three tools
- [backend/tools/demo_tools.py](../backend/tools/demo_tools.py) - CLI runner for testing tools without an MCP client
- [backend/requirements.txt](../backend/requirements.txt) - dependency list, including `mcp[cli]`
- [docs/data_architecture.md](data_architecture.md) - data model explanation
- [docs/Project Chunks.md](Project%20Chunks.md) - full locked blueprint
- [docs/ai_dev_log.md](ai_dev_log.md) - work log and completion history

## Will It Work With Fake Data?

Yes, for the support DB and MCP tool flow, fake data is expected.

The system does not require real customer records to function. It needs:

- a valid Postgres schema and seed data
- a doc chunk table with embeddings
- a working issue tracker client
- a routing layer that chooses the right tool

So the fact that the support data is synthetic is not a blocker. It is the intended setup for a portfolio project.

What would not work is expecting fake data to behave like a real production environment without matching the schema and the relationships. That is why the seed script was designed to keep the story coherent.

## What You Should Study Before Chunk 5

You do not need deep theory first. You need enough understanding to build the router correctly.

### 1. SQL basics for support data

Learn:

- `SELECT`, `JOIN`, `WHERE`, `GROUP BY`
- foreign keys and one-to-many relationships
- how to read a schema and trace `customer -> organization -> project -> ticket`

Why it matters:

- Chunk 5 will route account questions to SQL first.

### 2. RLS

Learn:

- what row-level security is
- why it limits which rows a user can read
- the idea of policies that allow or block access

Why it matters:

- Supabase docs use RLS constantly.
- The docs tool will often need to answer questions about it.

### 3. Vector embeddings and `pgvector`

Learn:

- what an embedding is in plain language
- why similar text ends up with nearby vectors
- why `pgvector` lets Postgres do similarity search

Why it matters:

- this is the core of `search_docs`
- Chunk 5 may need to know when a question is a docs question instead of a database question

### 4. MCP

Learn:

- MCP means Model Context Protocol
- it standardizes how tools are exposed to an AI model
- the server publishes tools and the agent calls them

Why it matters:

- Chunk 4 already exposed the tools through MCP
- Chunk 5 will use those tools through an orchestrator, not directly

### 5. Routing / orchestration

Learn:

- how to classify a user question
- when to call one tool
- when to call two tools in sequence
- how to stop and say "I do not know" if no source answers the question

Why it matters:

- Chunk 5 is the logic that decides which tool to call for each question
- the hardest case is a mixed question that needs SQL and issue tracker together

## Chunk 5 Mental Model

Chunk 5 is not about new data.

It is about the decision loop:

1. read the user question
2. decide which tool or tools to call
3. call them in the right order
4. combine the results into one answer
5. cite the source used

If you can explain why a question goes to SQL, docs, issue tracker, or a combination, you are ready for Chunk 5.

## Fast Readiness Check

You are ready to start Chunk 5 if you can answer these three prompts:

- When should the copilot use the support database?
- When should it search docs instead?
- When should it check the live issue tracker, or both docs and SQL?

If that is clear, the next build step is the orchestrator.