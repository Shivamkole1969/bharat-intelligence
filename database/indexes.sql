-- ============================================================
-- Bharat Market Intelligence Agent — Database Indexes
-- Run after schema.sql
-- ============================================================

-- Companies
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);
CREATE INDEX IF NOT EXISTS idx_companies_nse_symbol ON companies(nse_symbol);
CREATE INDEX IF NOT EXISTS idx_companies_bse_code ON companies(bse_code);

-- Raw Documents
CREATE INDEX IF NOT EXISTS idx_raw_documents_company ON raw_documents(company_id);
CREATE INDEX IF NOT EXISTS idx_raw_documents_published ON raw_documents(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_documents_hash ON raw_documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_raw_documents_type ON raw_documents(document_type);

-- Market Events
CREATE INDEX IF NOT EXISTS idx_market_events_company ON market_events(company_id);
CREATE INDEX IF NOT EXISTS idx_market_events_type ON market_events(event_type);
CREATE INDEX IF NOT EXISTS idx_market_events_time ON market_events(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_market_events_impact ON market_events(impact_label);
CREATE INDEX IF NOT EXISTS idx_market_events_material ON market_events(is_material);
CREATE INDEX IF NOT EXISTS idx_market_events_detected ON market_events(detected_at DESC);

-- Document Chunks
CREATE INDEX IF NOT EXISTS idx_chunks_company ON document_chunks(company_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);

-- Chat
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);

-- Audit
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);

-- Signal Scores
CREATE INDEX IF NOT EXISTS idx_stock_signal_scores_date ON stock_signal_scores(score_date DESC);
CREATE INDEX IF NOT EXISTS idx_stock_signal_scores_bullish ON stock_signal_scores(bullish_score DESC);
CREATE INDEX IF NOT EXISTS idx_stock_signal_scores_bearish ON stock_signal_scores(bearish_score DESC);
CREATE INDEX IF NOT EXISTS idx_stock_signal_scores_company ON stock_signal_scores(company_id);

-- Theses
CREATE INDEX IF NOT EXISTS idx_stock_theses_company ON stock_theses(company_id);
CREATE INDEX IF NOT EXISTS idx_stock_theses_type ON stock_theses(thesis_type);

-- Watchlists
CREATE INDEX IF NOT EXISTS idx_watchlist_companies_watchlist ON watchlist_companies(watchlist_id);

-- API Key Usage
CREATE INDEX IF NOT EXISTS idx_api_key_usage_key ON api_key_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_key_usage_created ON api_key_usage(created_at DESC);

-- Vector indexes (IVFFlat for pgvector)
-- NOTE: Run AFTER inserting initial data for better index quality.
-- For small datasets, use exact search first; add index when > 10k chunks.
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding
    ON semantic_cache
    USING ivfflat (query_embedding vector_cosine_ops)
    WITH (lists = 50);
