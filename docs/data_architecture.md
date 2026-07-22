# Data Architecture

The Enterprise Data Copilot operates across three distinct knowledge sources to mimic a realistic support environment for a Backend-as-a-Service (BaaS) platform (specifically modeled after Supabase). This document outlines the structure, purpose, and integration of each data source.

---

## 1. SQL Database

The structured database represents the operational backend of the BaaS platform. It tracks the hierarchy of customers, organizations, projects, usage metrics, billing, and support history.

### ER-Style Hierarchy

```text
Customer
  └─ Organization
       ├─ Subscriptions
       ├─ Invoices
       └─ Projects
            ├─ Usage Metrics
            └─ Tickets
                 └─ Ticket Messages
```

### Business Entities & Table Relationships

*   **Customers**: The physical individuals who register on the platform. Includes name, email, timezone, and country.
*   **Organizations**: The logical billing and grouping entity. A customer can own multiple organizations. Contains `billing_email`.
*   **Projects**: Represents an individual database, app, or environment. Owned by an organization. Contains `project_ref` (unique identifier), `region`, `postgres_version`, and `status`.
*   **Usage Metrics**: A 1-to-1 relationship with Projects. Tracks platform consumption such as `database_size_gb`, `storage_gb`, `bandwidth_gb`, and `api_requests`.
*   **Subscriptions & Invoices**: Tied directly to Organizations. Determines plan levels (`free`, `pro`, `team`, `enterprise`) and tracks payment history.
*   **Tickets & Ticket Messages**: The support history. Tickets are opened by a Customer, usually tied to a specific Project, and handled by an Agent. They track the `affected_product` (e.g., Auth, Storage, Database) to help agents route issues.

### Why Each Table Exists
The separation of Customers, Organizations, and Projects allows the Copilot to answer complex, hierarchical support questions. For example, a customer might have a failing invoice on one organization, but their project in a *different* organization is functioning fine. This models real-world B2B SaaS complexity.

### Example Support Queries
*   "What is the current database size of project `abcdefghijklmnopqr`?"
*   "Show me all past-due invoices for organizations owned by `alice@example.com`."
*   "How many urgent tickets are currently open regarding 'Edge Functions'?"

---

## 2. RAG Corpus

The RAG (Retrieval-Augmented Generation) corpus provides the Copilot with deep product knowledge. 

### Source
The documentation is sourced directly from the official **Supabase documentation repository**. This ensures the Copilot has access to realistic, production-grade technical guides rather than generic placeholder text.

### Ingestion & Processing Pipeline
1.  **Document Ingestion**: Markdown (`.md` and `.mdx`) files are read from the cloned repository. Frontmatter and MDX components are stripped to leave clean text.
2.  **Chunking**: The text is split into roughly 500-token chunks with a 50-token overlap to maintain context across boundaries.
3.  **Embeddings**: Each chunk is passed through a local embedding model (`sentence-transformers/all-MiniLM-L6-v2`) to generate a 384-dimensional vector.
4.  **Metadata**: Alongside the vector, metadata is stored to improve retrieval relevance:
    *   `title`, `product` (e.g., Auth, Storage), `section`, `url`, `chunk_index`, and `last_updated`.

### Retrieval Flow
When a user asks a technical "how-to" question, the question is embedded using the same `all-MiniLM-L6-v2` model. A similarity search (`<->` cosine distance) is executed against the `doc_chunks` table in Postgres using the `pgvector` extension. The top 5 most relevant chunks (with their metadata) are returned to the LLM to synthesize an answer.

---

## 3. External API

The Copilot integrates with a live external system to bridge the gap between internal data and ongoing engineering work.

### GitHub Issues API
We query the live `supabase/supabase` repository via the GitHub REST API. 

### Why It Is Used
Support agents frequently need to know if a customer's bug report is a known issue, if a feature has already been requested, or if there's a regression in a recent deployment. The API provides real-time access to the engineering team's public tracker.

### What Information It Provides
*   **Known Bugs**: Open issues that engineers are currently investigating.
*   **Feature Requests**: Community discussions about upcoming capabilities.
*   **Open Regressions**: Recently introduced bugs marked with specific labels.
*   **Workarounds & Maintainer Comments**: The actual discussion threads often contain temporary fixes or workarounds posted by maintainers, which the Copilot can summarize for the customer.

### Example Flow
1. Customer reports: "My OAuth callback is failing with invalid grant."
2. Copilot routes to the API tool: `search_issues(keyword="OAuth invalid grant callback")`.
3. Copilot retrieves an open issue: "#12453: OAuth callback fails intermittently on edge network".
4. Copilot responds to customer: "This is a known issue our engineering team is actively investigating (Issue #12453). A temporary workaround is to..."
