-- ============================================================
-- Enterprise Data Copilot — Database Schema
-- Chunk 1: Core business tables (customers, subscriptions, etc.)
-- Chunk 2: Document RAG storage (doc_chunks with pgvector)
-- Chunk 6: Conversation logging (conversations, turns)
-- ============================================================

-- Enable pgvector extension for document embeddings
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- CHUNK 1: Core Business Tables
-- ============================================================

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    company TEXT,
    signup_date DATE NOT NULL,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'pro', 'team', 'enterprise'))
);

CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    plan_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'past_due', 'cancelled', 'trialing')),
    mrr NUMERIC(10,2) NOT NULL,
    renewal_date DATE,
    started_at DATE NOT NULL
);

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    amount NUMERIC(10,2) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('paid', 'pending', 'failed', 'refunded')),
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
    customer_id INTEGER REFERENCES customers(id),
    agent_id INTEGER REFERENCES agents(id),
    subject TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('billing', 'technical', 'account', 'feature_request', 'bug')),
    status TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    resolved_at TIMESTAMP
);

CREATE TABLE ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    sender_type TEXT NOT NULL CHECK (sender_type IN ('customer', 'agent')),
    message TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- ============================================================
-- CHUNK 2: Document RAG Storage (pgvector)
-- ============================================================

CREATE TABLE doc_chunks (
    id SERIAL PRIMARY KEY,
    source_file TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384)  -- 384 = all-MiniLM-L6-v2 output dimension
);

-- Index for fast similarity search
CREATE INDEX ON doc_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- CHUNK 6: Conversation Logging
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
    created_at TIMESTAMP DEFAULT now()
);
