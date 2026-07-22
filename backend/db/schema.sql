-- ============================================================
-- Enterprise Data Copilot — Database Schema (SaaS/BaaS Model)
-- Models a hierarchy: Customer -> Organization -> Project -> Usage
-- Includes Support Tickets, RAG storage, and Conversation logging
-- ============================================================

-- Enable pgvector extension for document embeddings
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- CORE BUSINESS ENTITIES
-- ============================================================

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

-- ============================================================
-- BILLING ENTITIES
-- ============================================================

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

-- ============================================================
-- SUPPORT TICKETING
-- ============================================================

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

-- ============================================================
-- DOCUMENT RAG STORAGE (pgvector)
-- ============================================================

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

-- Index for fast similarity search
CREATE INDEX ON doc_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- CONVERSATION LOGGING
-- ============================================================

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE turns (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tool_calls JSONB,
    tool_name TEXT,
    latency_ms INTEGER,
    token_usage INTEGER,
    created_at TIMESTAMP DEFAULT now()
);
