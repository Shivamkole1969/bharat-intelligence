-- ============================================================
-- Bharat Market Intelligence Agent — Database Schema
-- Supabase Postgres with pgvector
-- ============================================================
-- Run this once to create all tables.
-- Requires: CREATE EXTENSION IF NOT EXISTS vector;
--           CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. companies
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    isin TEXT,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    market_cap NUMERIC,
    website TEXT,
    bse_code TEXT,
    nse_symbol TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(exchange, symbol)
);

-- ============================================================
-- 2. data_sources
-- ============================================================
CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    reliability_score NUMERIC DEFAULT 0.80,
    license_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3. raw_documents
-- ============================================================
CREATE TABLE IF NOT EXISTS raw_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(id),
    company_id UUID REFERENCES companies(id),
    document_type TEXT NOT NULL,
    title TEXT,
    url TEXT,
    raw_text TEXT,
    raw_html TEXT,
    file_path TEXT,
    published_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    content_hash TEXT UNIQUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- ============================================================
-- 4. document_chunks
-- ============================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES raw_documents(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INT,
    embedding VECTOR(384),
    section_title TEXT,
    page_number INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 5. market_events
-- ============================================================
CREATE TABLE IF NOT EXISTS market_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    source_document_id UUID REFERENCES raw_documents(id),
    event_type TEXT NOT NULL,
    event_subtype TEXT,
    event_title TEXT NOT NULL,
    event_summary TEXT,
    impact_label TEXT,
    impact_score NUMERIC,
    confidence_score NUMERIC,
    sentiment_score NUMERIC,
    severity TEXT,
    event_time TIMESTAMPTZ,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    source_url TEXT,
    entities JSONB DEFAULT '{}'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb,
    is_material BOOLEAN DEFAULT FALSE,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 6. event_citations
-- ============================================================
CREATE TABLE IF NOT EXISTS event_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES market_events(id) ON DELETE CASCADE,
    document_id UUID REFERENCES raw_documents(id),
    chunk_id UUID REFERENCES document_chunks(id),
    citation_text TEXT,
    source_url TEXT,
    page_number INT,
    confidence_score NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 7. users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE,
    display_name TEXT,
    auth_provider TEXT,
    plan TEXT DEFAULT 'free',
    daily_chat_limit INT DEFAULT 20,
    daily_alert_limit INT DEFAULT 20,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ
);

-- ============================================================
-- 8. watchlists
-- ============================================================
CREATE TABLE IF NOT EXISTS watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 9. watchlist_companies
-- ============================================================
CREATE TABLE IF NOT EXISTS watchlist_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
    alert_threshold TEXT DEFAULT 'medium',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(watchlist_id, company_id)
);

-- ============================================================
-- 10. chat_sessions
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_title TEXT,
    mode TEXT DEFAULT 'general_market',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 11. chat_messages
-- ============================================================
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    model_used TEXT,
    cost_estimate NUMERIC,
    latency_ms INT,
    confidence_score NUMERIC,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 12. llm_api_keys (metadata only — keys encrypted)
-- ============================================================
CREATE TABLE IF NOT EXISTS llm_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    key_alias TEXT NOT NULL,
    encrypted_key TEXT NOT NULL,
    daily_token_limit BIGINT,
    used_tokens_today BIGINT DEFAULT 0,
    rpm_limit INT,
    tpm_limit INT,
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 1,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 13. api_key_usage
-- ============================================================
CREATE TABLE IF NOT EXISTS api_key_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES llm_api_keys(id),
    request_id UUID,
    provider TEXT,
    model TEXT,
    input_tokens INT,
    output_tokens INT,
    cost_estimate NUMERIC,
    status TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 14. audit_logs (append-only with hash chaining)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_type TEXT NOT NULL,
    actor_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    input_hash TEXT,
    output_hash TEXT,
    previous_hash TEXT,
    current_hash TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 15. eval_runs
-- ============================================================
CREATE TABLE IF NOT EXISTS eval_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eval_type TEXT NOT NULL,
    dataset_name TEXT,
    model_name TEXT,
    prompt_version TEXT,
    rag_pipeline_version TEXT,
    score NUMERIC,
    passed BOOLEAN,
    report JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 16. system_health
-- ============================================================
CREATE TABLE IF NOT EXISTS system_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INT,
    error_rate NUMERIC,
    queue_lag INT,
    metadata JSONB DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 17. stock_signal_scores
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_signal_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    score_date DATE NOT NULL,
    bullish_score NUMERIC DEFAULT 0,
    bearish_score NUMERIC DEFAULT 0,
    quality_score NUMERIC DEFAULT 0,
    momentum_score NUMERIC DEFAULT 0,
    valuation_risk_score NUMERIC DEFAULT 0,
    governance_risk_score NUMERIC DEFAULT 0,
    news_sentiment_score NUMERIC DEFAULT 0,
    event_strength_score NUMERIC DEFAULT 0,
    confidence_score NUMERIC DEFAULT 0,
    explanation TEXT,
    top_positive_factors JSONB DEFAULT '[]'::jsonb,
    top_negative_factors JSONB DEFAULT '[]'::jsonb,
    source_event_ids JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(company_id, score_date)
);

-- ============================================================
-- 18. stock_theses
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_theses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    thesis_type TEXT NOT NULL,
    thesis_title TEXT NOT NULL,
    thesis_summary TEXT NOT NULL,
    supporting_points JSONB DEFAULT '[]'::jsonb,
    risks JSONB DEFAULT '[]'::jsonb,
    counterpoints JSONB DEFAULT '[]'::jsonb,
    citations JSONB DEFAULT '[]'::jsonb,
    confidence_score NUMERIC,
    generated_by_model TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 19. semantic_cache
-- ============================================================
CREATE TABLE IF NOT EXISTS semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_query TEXT NOT NULL,
    query_embedding VECTOR(384),
    answer TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    mode TEXT,
    company_id UUID REFERENCES companies(id),
    fresh_until TIMESTAMPTZ,
    hit_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
