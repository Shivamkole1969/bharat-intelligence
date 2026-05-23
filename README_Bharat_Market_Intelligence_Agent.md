# Bharat Market Intelligence Agent

> Real-time Indian financial intelligence platform with streaming ingestion, multi-agent research, citation-grounded chatbot answers, investor dashboards, governance, audit logs, and scalable deployment architecture.

---

## 1. Project Summary

**Bharat Market Intelligence Agent** is a production-grade AI + data engineering project for Indian financial markets.

It continuously tracks:

- NSE/BSE corporate announcements
- Company filings
- Annual reports
- Earnings call transcripts
- Investor presentations
- Public market news
- RBI/SEBI/government releases
- Sector-level events
- Delayed/free market data where legally available
- Macro indicators
- Commodity and currency signals where available

The system converts raw public information into:

- Structured market events
- Company intelligence pages
- Watchlist alerts
- Source-cited AI summaries
- Risk flags
- Bullish and bearish opportunity watchlists
- Chatbot answers with citations
- Audit logs
- Evaluation reports
- System health dashboards

This project is designed to show real production engineering ability, not just a simple AI chatbot.

---

## 2. Important Compliance Disclaimer

This application is for **educational, research, and informational purposes only**.

It must not provide personalized investment advice, guaranteed returns, target prices, or direct buy/sell/short recommendations.

Instead of saying:

> Buy this stock.

The system should say:

> This stock is currently appearing in the bullish watchlist because of public signals such as positive earnings commentary, strong order wins, improving margins, or positive sector momentum. This is not investment advice. Please verify independently and consult a SEBI-registered adviser before making investment decisions.

Instead of saying:

> Short this stock.

The system should say:

> This stock is currently appearing in the bearish risk watchlist because of public signals such as weak earnings, rating downgrade, governance concern, debt stress, or negative news. This is not a short-selling recommendation.

Use safe labels:

- **Bullish Watchlist**
- **Bearish Risk Watchlist**
- **Positive Signal Candidates**
- **Negative Risk Candidates**
- **Stocks to Research Further**
- **High-Risk / High-Volatility Candidates**

Avoid unsafe labels in production UI:

- Best stocks to buy
- Guaranteed winners
- Sure shot multibagger
- Stocks to short now
- Intraday tips
- Buy/sell calls

---

## 3. Core Product Vision

Indian investors, analysts, students, and small advisory teams cannot monitor thousands of public market events every day.

Important information is scattered across:

- Exchange announcements
- Company PDFs
- News articles
- Financial statements
- Earnings transcripts
- Investor presentations
- Credit rating updates
- Regulatory circulars
- Sector reports
- Macro releases

This platform acts like a **junior financial research analyst that never sleeps**.

It tracks public information, detects important events, explains why they matter, gives source citations, and allows users to ask questions in natural language.

---

## 4. Target Users

### 4.1 Retail Investors

Users who want simple explanations of market events.

### 4.2 Students and Learners

Users learning equity research, financial analysis, and market behavior.

### 4.3 Small Advisory Teams

Teams that want a monitoring and research assistant.

### 4.4 Analysts

Users who want fast source-grounded summaries.

### 4.5 Portfolio Trackers

Users who want alerts for selected companies.

### 4.6 Recruiters and Hiring Managers

They should see that this is a real distributed AI system with data pipelines, agents, evaluation, observability, and deployment design.

---

## 5. Main Capabilities

- Real-time/event-driven ingestion
- NSE/BSE announcement tracking
- Public news ingestion
- Company document ingestion
- Annual report and PDF parsing
- Earnings transcript intelligence
- Company-level RAG
- Sector-level intelligence
- Multi-agent event classification
- Financial impact explanation
- Citation verification
- Watchlist alerts
- Bullish watchlist
- Bearish risk watchlist
- AI chatbot
- API-key-independent fallback chatbot
- Groq API key routing
- Local open-source model fallback
- Redis caching
- Semantic answer cache
- SQL-first answers
- Template-first answers
- Deep research mode
- Public dashboard
- Company intelligence pages
- 3D animated market map
- Audit logs with hash chaining
- Langfuse tracing
- DeepEval evaluation
- RAGAS evaluation
- Promptfoo prompt/security tests
- Evidently drift monitoring
- MLflow experiment tracking
- Prometheus/Grafana observability
- Docker Compose
- Kubernetes-ready architecture
- GitHub Actions CI/CD

---

## 6. What Makes This Project Different

Most AI portfolio projects are:

- Chatbot only
- No real data pipeline
- No observability
- No evaluation
- No database design
- No scalable architecture
- No compliance layer
- No audit logs
- No fallback when LLM APIs fail

This project includes:

- Streaming data architecture
- Real database schema
- AI governance
- LLM cost optimization
- Agent workflows
- Market event intelligence
- Public-user scaling design
- Offline/local fallback chatbot
- Proper financial compliance guardrails

---

## 7. High-Level Architecture

```text
                         ┌──────────────────────────────┐
                         │          Public Users          │
                         │ Investors / Analysts / Guests  │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                         ┌──────────────────────────────┐
                         │ HTML + CSS + JavaScript UI    │
                         │ Vercel + 3D Animations        │
                         └───────────────┬──────────────┘
                                         │
                                         ▼
                         ┌──────────────────────────────┐
                         │ FastAPI API Gateway           │
                         │ Auth / Rate Limit / Cache     │
                         └───────┬───────────────┬──────┘
                                 │               │
                                 ▼               ▼
                  ┌─────────────────────┐ ┌──────────────────────┐
                  │ Chatbot Service      │ │ Market Intelligence   │
                  │ RAG + Fallbacks      │ │ APIs + Dashboards     │
                  └──────────┬──────────┘ └───────────┬──────────┘
                             │                        │
                             ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LangGraph Agent Layer                        │
│ Ingestion Agent                                                      │
│ Deduplication Agent                                                  │
│ Event Classification Agent                                           │
│ Financial Impact Agent                                               │
│ Citation Verification Agent                                          │
│ Compliance Guardrail Agent                                           │
│ Alert Agent                                                          │
│ Bullish/Bearish Ranking Agent                                        │
│ Chat Router Agent                                                    │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Streaming + Processing Layer                    │
│ Redpanda / Kafka Topics                                              │
│ Airflow / Dagster Scheduled Jobs                                     │
│ Async Python Workers                                                 │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Storage Layer                              │
│ Supabase Postgres                                                    │
│ pgvector                                                             │
│ Redis                                                                │
│ Object Storage                                                       │
│ Append-only Audit Logs                                               │
│ Optional Qdrant Later                                                │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Evaluation + Observability Layer                  │
│ Langfuse                                                             │
│ DeepEval                                                             │
│ RAGAS                                                                │
│ Promptfoo                                                            │
│ Evidently AI                                                         │
│ MLflow                                                               │
│ Prometheus                                                           │
│ Grafana                                                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Application Pages

### 8.1 Landing Page

Goal: Explain the product instantly.

Sections:

- 3D animated India market network
- Live intelligence preview
- Ask the AI Analyst demo
- Key features
- Data sources
- Trust and citation explanation
- Disclaimer
- CTA to dashboard

Recommended UI text:

```text
Real-time AI intelligence for Indian markets.
Track announcements, filings, news, risks, and opportunities with cited AI summaries.
```

---

### 8.2 Live Intelligence Dashboard

Goal: Show what is happening now.

Features:

- Latest corporate announcements
- Latest news events
- Market-moving alerts
- Sector heatmap
- Positive signal events
- Negative risk events
- Confidence score
- Source links
- Event freshness
- AI-generated event summaries

Card example:

```text
Company: Tata Motors
Event Type: Earnings Commentary
Impact: Positive
Severity: Medium
Confidence: 87%
Freshness: 5 minutes ago
Source: Exchange announcement / news / transcript

Summary:
...

Why it matters:
...
```

---

### 8.3 Company Intelligence Page

Goal: One-page research view for each company.

Features:

- Company overview
- Latest announcements
- Latest news
- Financial highlights
- Key risks
- Management events
- Peer comparison
- Event timeline
- Chat with company data
- Source citations
- Bullish thesis
- Bearish thesis
- News related to the thesis
- Data freshness status

User questions:

```text
What changed for this company in the last 7 days?
What are the latest risk events?
Explain latest announcement in simple language.
Compare this company with its peers.
Show only source-backed facts.
What is the bullish thesis?
What is the bearish thesis?
```

---

### 8.4 Watchlist Page

Goal: Let users track companies.

Features:

- Add/remove companies
- Watchlist alerts
- Alert threshold
- Risk category filters
- Positive/negative events
- Browser/email notification later
- Why this alert appeared

Alert categories:

- Earnings
- Rating downgrade
- Rating upgrade
- Management change
- Pledge change
- Fraud risk
- Litigation
- Order win
- Acquisition
- Debt issue
- Insolvency
- Auditor comment
- Dividend
- Split/bonus
- Regulatory action
- Sector macro event

---

### 8.5 AI Chatbot Page

Goal: Let users interact with the market intelligence system.

Modes:

1. General Market Mode
2. Company Mode
3. Watchlist Mode
4. Education Mode
5. Source-only Mode
6. Low-cost Mode
7. Deep Research Mode
8. Offline Fallback Mode

Response format:

```text
Answer:
...

Evidence:
1. Source
2. Published timestamp
3. Relevant snippet
4. Link/reference

Confidence:
High / Medium / Low

Limitations:
...

Disclaimer:
This is informational and not investment advice.
```

---

### 8.6 Bullish Watchlist Page

Goal: Show top positive-signal companies to research.

Safe title:

```text
Top 10 Bullish Signal Candidates
```

Not safe title:

```text
Top 10 Best Stocks to Buy
```

Features:

- Top 10 positive-signal candidates
- Score breakdown
- Thesis summary
- Related news
- Related announcements
- Risk factors
- Confidence score
- Data freshness
- Click company for full thesis

Ranking criteria:

- Positive earnings surprise
- Strong revenue/margin trend
- Order wins
- Positive management commentary
- Rating upgrade
- Debt reduction
- Positive sector momentum
- Strong institutional/news signal
- Low controversy score
- Improving financial metrics

Example card:

```text
Rank: 1
Company: Example Ltd
Signal: Positive order win + margin improvement
Bullish Score: 82/100
Confidence: Medium
Thesis:
The company appears in the bullish watchlist because recent public announcements indicate order inflow, improved management commentary, and positive sector demand.
Risks:
Execution risk, valuation risk, sector cyclicality.
Sources:
...
```

---

### 8.7 Bearish Risk Watchlist Page

Goal: Show top negative-risk companies to research.

Safe title:

```text
Top 10 Bearish Risk Candidates
```

Not safe title:

```text
Top 10 Stocks to Short
```

Features:

- Top 10 negative-risk candidates
- Risk score
- Bearish thesis
- Related news
- Related announcements
- Counterpoints
- Confidence score
- Data freshness
- Click company for full risk analysis

Ranking criteria:

- Weak earnings
- Margin pressure
- Rating downgrade
- High debt warning
- Auditor resignation/comment
- Promoter pledge increase
- Litigation/regulatory action
- Negative management commentary
- Sector pressure
- Unusual negative news volume
- Governance concern

Example card:

```text
Rank: 1
Company: Example Ltd
Signal: Rating downgrade + debt stress
Bearish Risk Score: 86/100
Confidence: High
Bearish Thesis:
The company appears in the bearish risk watchlist because recent public sources indicate rising leverage, weak cash flow commentary, and negative rating action.
Counterpoints:
Potential asset sale, possible refinancing, sector recovery.
Sources:
...
```

---

### 8.8 3D Market Map Page

Goal: Visual and impressive representation of market intelligence.

Features:

- Sectors as 3D clusters
- Companies as nodes
- Node size by event volume or market cap
- Node color by signal score
- Pulsing animation for fresh events
- Click company to open intelligence page
- Hover to see latest event

Tech:

- Three.js
- D3.js
- WebSocket/SSE updates
- CSS glassmorphism

---

### 8.9 Data Quality & Audit Page

Goal: Show trust.

Features:

- Source freshness
- Last successful ingestion time
- Failed jobs
- Duplicate event count
- Citation coverage
- RAG faithfulness score
- Hallucination score
- Eval pass rate
- Audit log hash chain
- Data lineage

---

### 8.10 Admin/Ops Page

Goal: Monitor and operate the system.

Features:

- API key usage
- Groq key rotation status
- LLM provider health
- Queue length
- Kafka lag
- Worker failures
- Failed event retry
- Cache hit ratio
- Cost estimate
- Model usage
- Prompt version
- Eval version
- Deployment version
- System health

---

## 9. Data Sources

### 9.1 MVP Data Sources

Use legal, public, or free sources first:

- BSE corporate announcements
- NSE corporate announcements where available
- Company investor relations pages
- Annual reports
- Earnings call transcripts
- Public RSS feeds
- RBI releases
- SEBI circulars
- Government macro data
- Delayed/free price APIs for demo
- Yahoo Finance / yfinance for educational demo only
- Alpha Vantage / Twelve Data free tier if available

### 9.2 Production Data Sources

For production-grade real-time market prices:

- Official exchange feeds
- Licensed data vendors
- Paid market data APIs

Do not illegally scrape or redistribute licensed exchange data.

---

## 10. Data Philosophy

Every data item must have:

- Source name
- Source URL
- Source type
- Published timestamp
- Ingested timestamp
- Company mapping
- Content hash
- Processing status
- Confidence score
- Citation mapping
- Audit trace

Good data is more important than fancy AI.

---

## 11. Database Architecture

Main database:

- Supabase Postgres

Vector search:

- pgvector first
- Qdrant later if scale increases

Cache:

- Redis

Raw files:

- Object storage

Audit:

- Append-only Postgres audit logs with hash chaining

---

## 12. Database Tables

### 12.1 companies

```sql
CREATE TABLE companies (
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
```

### 12.2 data_sources

```sql
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    reliability_score NUMERIC DEFAULT 0.80,
    license_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 12.3 raw_documents

```sql
CREATE TABLE raw_documents (
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
```

### 12.4 document_chunks

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES raw_documents(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INT,
    embedding VECTOR(1536),
    section_title TEXT,
    page_number INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 12.5 market_events

```sql
CREATE TABLE market_events (
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
```

### 12.6 event_citations

```sql
CREATE TABLE event_citations (
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
```

### 12.7 users

```sql
CREATE TABLE users (
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
```

### 12.8 watchlists

```sql
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 12.9 watchlist_companies

```sql
CREATE TABLE watchlist_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watchlist_id UUID REFERENCES watchlists(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
    alert_threshold TEXT DEFAULT 'medium',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(watchlist_id, company_id)
);
```

### 12.10 chat_sessions

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_title TEXT,
    mode TEXT DEFAULT 'general_market',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 12.11 chat_messages

```sql
CREATE TABLE chat_messages (
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
```

### 12.12 llm_api_keys

Use this for metadata only. Do not expose keys to frontend.

```sql
CREATE TABLE llm_api_keys (
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
```

### 12.13 api_key_usage

```sql
CREATE TABLE api_key_usage (
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
```

### 12.14 audit_logs

```sql
CREATE TABLE audit_logs (
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
```

### 12.15 eval_runs

```sql
CREATE TABLE eval_runs (
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
```

### 12.16 system_health

```sql
CREATE TABLE system_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INT,
    error_rate NUMERIC,
    queue_lag INT,
    metadata JSONB DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 12.17 stock_signal_scores

Stores bullish and bearish ranking scores.

```sql
CREATE TABLE stock_signal_scores (
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
```

### 12.18 stock_theses

Stores generated bullish/bearish thesis.

```sql
CREATE TABLE stock_theses (
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
```

### 12.19 semantic_cache

```sql
CREATE TABLE semantic_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    normalized_query TEXT NOT NULL,
    query_embedding VECTOR(1536),
    answer TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    mode TEXT,
    company_id UUID REFERENCES companies(id),
    fresh_until TIMESTAMPTZ,
    hit_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 13. Database Indexes

```sql
CREATE INDEX idx_companies_symbol ON companies(symbol);
CREATE INDEX idx_companies_sector ON companies(sector);

CREATE INDEX idx_raw_documents_company ON raw_documents(company_id);
CREATE INDEX idx_raw_documents_published ON raw_documents(published_at DESC);
CREATE INDEX idx_raw_documents_hash ON raw_documents(content_hash);

CREATE INDEX idx_market_events_company ON market_events(company_id);
CREATE INDEX idx_market_events_type ON market_events(event_type);
CREATE INDEX idx_market_events_time ON market_events(event_time DESC);
CREATE INDEX idx_market_events_impact ON market_events(impact_label);
CREATE INDEX idx_market_events_material ON market_events(is_material);

CREATE INDEX idx_chunks_company ON document_chunks(company_id);
CREATE INDEX idx_chunks_document ON document_chunks(document_id);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

CREATE INDEX idx_stock_signal_scores_date ON stock_signal_scores(score_date DESC);
CREATE INDEX idx_stock_signal_scores_bullish ON stock_signal_scores(bullish_score DESC);
CREATE INDEX idx_stock_signal_scores_bearish ON stock_signal_scores(bearish_score DESC);
```

Vector index:

```sql
CREATE INDEX document_chunks_embedding_idx
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 14. Streaming Topic Design

Use Redpanda locally because it is Kafka-compatible and simpler for development.

Topics:

```text
raw.bse.announcements
raw.nse.announcements
raw.news
raw.filings
raw.earnings_transcripts
raw.prices.delayed
raw.macro

parsed.documents
deduped.documents
classified.events
embedded.chunks
scored.events
ranked.signals
alerts.generated

chat.requests
chat.responses

eval.requests
eval.results

deadletter.events
```

---

## 15. Event Message Schema

```json
{
  "event_id": "uuid",
  "source": "bse",
  "source_url": "https://example.com",
  "company_symbol": "RELIANCE",
  "exchange": "BSE",
  "document_type": "announcement",
  "title": "Board Meeting Outcome",
  "raw_text": "...",
  "published_at": "2026-05-22T10:30:00+05:30",
  "ingested_at": "2026-05-22T10:31:00+05:30",
  "content_hash": "sha256...",
  "metadata": {}
}
```

---

## 16. Agent Architecture

### 16.1 Ingestion Agent

Responsibilities:

- Pull public data
- Normalize documents
- Generate content hash
- Store raw documents
- Publish to streaming topic
- Log audit entry

Failure behavior:

- Retry 3 times
- Exponential backoff
- Send to dead-letter queue
- Continue other sources

---

### 16.2 Deduplication Agent

Responsibilities:

- Remove duplicate announcements
- Remove repeated news
- Merge similar events

Methods:

- Content hash
- URL hash
- Title similarity
- Embedding similarity
- Company + timestamp window

---

### 16.3 Event Classification Agent

Responsibilities:

- Classify raw document into event type
- Extract event subtype
- Identify impact label
- Assign severity
- Assign confidence score

Output:

```json
{
  "event_type": "rating_change",
  "event_subtype": "downgrade",
  "impact_label": "negative",
  "severity": "high",
  "confidence_score": 0.91,
  "is_material": true,
  "summary": "...",
  "entities": ["company", "rating agency"],
  "metrics": {}
}
```

---

### 16.4 Financial Impact Agent

Responsibilities:

- Explain business impact
- Map event to financial metrics
- Identify risks
- Identify opportunities

Impact dimensions:

- Revenue impact
- Margin impact
- Debt impact
- Liquidity impact
- Governance risk
- Regulatory risk
- Valuation risk
- Sector impact

---

### 16.5 Citation Verification Agent

Responsibilities:

- Check claims against source chunks
- Attach citations
- Reject unsupported claims
- Score faithfulness

---

### 16.6 Compliance Guardrail Agent

Responsibilities:

- Avoid personalized financial advice
- Avoid buy/sell/short recommendations
- Add disclaimers
- Block unsafe queries
- Rewrite risky answers into informational form

Unsafe query examples:

```text
Tell me exactly which stock to buy.
Give me guaranteed multibagger.
Should I invest my salary?
Which stock should I short with leverage?
Give me insider information.
```

Safe response:

```text
I can summarize public signals, risks, and recent events, but I cannot provide personalized investment advice or guaranteed recommendations.
```

---

### 16.7 Alert Agent

Responsibilities:

- Match events to watchlists
- Generate alerts
- Push dashboard updates
- Queue email/push alerts later

---

### 16.8 Bullish/Bearish Ranking Agent

Responsibilities:

- Score companies daily or intraday
- Generate top bullish signal candidates
- Generate top bearish risk candidates
- Create thesis summaries
- Attach citations
- Include counterpoints and risks

Inputs:

- Market events
- News sentiment
- Financial metrics
- Earnings events
- Rating changes
- Management commentary
- Sector signals
- Governance events
- Price/volume signals where legally available

Output:

```json
{
  "company": "Example Ltd",
  "bullish_score": 82,
  "bearish_score": 21,
  "confidence_score": 76,
  "top_positive_factors": [
    "Recent order win",
    "Improving margin commentary",
    "Positive sector demand"
  ],
  "top_negative_factors": [
    "Execution risk",
    "Valuation risk"
  ],
  "thesis": "...",
  "citations": []
}
```

---

### 16.9 Chat Router Agent

Responsibilities:

- Decide how to answer user query
- Use cache first
- Use SQL/template when possible
- Use RAG when needed
- Use Groq only when necessary
- Use local fallback when keys fail
- Return source-backed answers

Routing order:

```text
1. Safety/compliance check
2. Exact cache lookup
3. Semantic cache lookup
4. SQL/database answer
5. Template answer
6. RAG answer
7. Groq LLM answer
8. Local model answer
9. Fallback source-only answer
```

---

## 17. Bullish/Bearish Ranking System

### 17.1 Why Not Direct Buy/Short Calls

The system must not act as an unregistered adviser.

Instead of:

```text
Top 10 stocks to buy
Top 10 stocks to short
```

Use:

```text
Top 10 Bullish Signal Candidates
Top 10 Bearish Risk Candidates
```

This keeps the system safer and more professional.

---

### 17.2 Bullish Score Formula

Initial simple version:

```text
bullish_score =
    0.20 * positive_event_score
  + 0.15 * earnings_quality_score
  + 0.15 * revenue_growth_signal
  + 0.10 * margin_signal
  + 0.10 * debt_improvement_signal
  + 0.10 * sector_momentum_score
  + 0.10 * news_sentiment_score
  + 0.05 * management_commentary_score
  + 0.05 * confidence_score
```

### 17.3 Bearish Score Formula

```text
bearish_score =
    0.20 * negative_event_score
  + 0.15 * debt_stress_score
  + 0.15 * earnings_weakness_score
  + 0.10 * governance_risk_score
  + 0.10 * rating_downgrade_score
  + 0.10 * litigation_or_regulatory_score
  + 0.10 * negative_news_sentiment_score
  + 0.05 * sector_pressure_score
  + 0.05 * confidence_score
```

---

### 17.4 Bullish Thesis Page

When user clicks a bullish candidate, show:

- Why this company appeared
- Latest supporting events
- Related news
- Financial metrics
- Positive thesis
- Key risks
- Counterpoints
- Confidence score
- Source citations
- Freshness timestamp
- Disclaimer

---

### 17.5 Bearish Risk Thesis Page

When user clicks a bearish candidate, show:

- Why this company appeared
- Latest risk events
- Related news
- Financial stress indicators
- Bearish thesis
- Counterpoints
- What could change the view
- Confidence score
- Source citations
- Freshness timestamp
- Disclaimer

---

## 18. Chatbot Without Depending on API Keys

The application must continue working even if all Groq API keys fail.

Use this layered design.

### 18.1 Layer 1: Static FAQ

No LLM required.

Examples:

- What is PE ratio?
- What is market cap?
- What is EBITDA?
- What is a corporate announcement?
- What is a rating downgrade?

Stored in Postgres or JSON.

---

### 18.2 Layer 2: Template-Based Answers

No LLM required.

Example:

User:

```text
Show latest events for Reliance.
```

System:

- Query database
- Fill template
- Return latest events and sources

---

### 18.3 Layer 3: SQL-First Answers

No LLM required.

Examples:

```text
Which companies had rating downgrades today?
Show top negative events in banking.
Show latest announcements for TCS.
```

---

### 18.4 Layer 4: Semantic Cache

No new LLM call if similar answer exists.

Flow:

```text
User query
→ Normalize query
→ Embed query
→ Search semantic_cache
→ If similarity high and answer fresh
→ Return cached answer
```

---

### 18.5 Layer 5: Local Embeddings

Use local sentence-transformer model for embeddings if paid API is unavailable.

Suggested models:

- sentence-transformers/all-MiniLM-L6-v2
- BAAI/bge-small-en-v1.5
- intfloat/e5-small-v2

---

### 18.6 Layer 6: Local LLM Fallback

If Groq is unavailable, use local or self-hosted models.

Options:

- Ollama locally
- llama.cpp
- vLLM if GPU available
- Small instruct model for fallback summaries

Suggested fallback models:

- Llama 3.1 8B Instruct
- Mistral 7B Instruct
- Gemma 2 9B Instruct
- Phi-3 Mini for lightweight fallback

For free local demo:

```text
Ollama + Llama 3.1 8B
```

---

### 18.7 Layer 7: Source-Only Fallback

If no LLM works:

Return:

- Matching source documents
- Extracted snippets
- Event table
- Links
- Confidence unavailable message

Example:

```text
The AI summarizer is temporarily unavailable.
Here are the most relevant source-backed events I found:
...
```

This means the chatbot still works even without API keys.

---

## 19. Groq API Key Strategy

You plan to use 10 Groq API keys.

Important rules:

- Never expose keys in frontend
- Store keys in backend secrets
- Rotate keys server-side
- Track usage per key
- Apply RPM/TPM limits
- Use circuit breakers
- Use fallback models
- Use cache before LLM call

### 19.1 LLM Router Logic

```python
def answer_query(query, user_id):
    safety = compliance_check(query)
    if not safety.allowed:
        return safety.safe_response

    cached = exact_cache_lookup(query)
    if cached:
        return cached

    semantic = semantic_cache_lookup(query)
    if semantic and semantic.is_fresh:
        return semantic.answer

    sql_answer = try_sql_answer(query)
    if sql_answer:
        return sql_answer

    template_answer = try_template_answer(query)
    if template_answer:
        return template_answer

    rag_context = retrieve_context(query)

    try:
        return groq_answer(query, rag_context)
    except Exception:
        pass

    try:
        return local_llm_answer(query, rag_context)
    except Exception:
        pass

    return source_only_answer(rag_context)
```

---

### 19.2 API Key Selection

```python
def select_groq_key(estimated_tokens):
    keys = get_active_groq_keys()

    healthy_keys = [
        key for key in keys
        if key.remaining_tokens_today > estimated_tokens
        and key.current_rpm < key.rpm_limit
        and key.current_tpm < key.tpm_limit
        and key.error_rate < 0.05
        and not key.in_cooldown
    ]

    if not healthy_keys:
        raise NoHealthyKeyAvailable()

    return sorted(
        healthy_keys,
        key=lambda k: (k.priority, k.used_tokens_today, k.avg_latency_ms)
    )[0]
```

---

## 20. Cost Control Strategy

The app should not burn API credits.

Use:

- Cached homepage summaries
- Precomputed daily market summary
- Precomputed company summaries
- Precomputed bullish/bearish theses
- SQL answers before LLM
- Template answers before LLM
- Semantic cache
- User quotas
- Anonymous-user limits
- Deep research queue
- Groq only for complex synthesis
- Local model fallback
- Short context windows
- Prompt compression
- Source filtering
- Daily batch summarization

---

## 21. Rate Limits

### Anonymous Users

```text
5 chatbot questions/day
Cached answers after limit
No deep research
```

### Free Logged-in Users

```text
20 chatbot questions/day
5 deep research questions/day
10 watchlist companies
```

### Demo/Admin User

```text
Higher limits for recruiter demos
```

### System-Level Limits

```text
Max concurrent LLM requests
Max tokens per request
Max deep research jobs per minute
Max API calls per IP
```

---

## 22. API Design

### Public APIs

```text
GET  /api/health
GET  /api/companies
GET  /api/companies/{symbol}
GET  /api/events/latest
GET  /api/events/company/{symbol}
GET  /api/events/sector/{sector}
GET  /api/market/summary
GET  /api/signals/bullish/top
GET  /api/signals/bearish/top
GET  /api/thesis/{symbol}
GET  /api/search
POST /api/chat
GET  /api/chat/sessions
GET  /api/watchlist
POST /api/watchlist
DELETE /api/watchlist/{id}
```

### Internal APIs

```text
POST /internal/ingest/bse
POST /internal/ingest/nse
POST /internal/ingest/news
POST /internal/process/document
POST /internal/process/event
POST /internal/rank/signals
POST /internal/eval/run
GET  /internal/admin/health
GET  /internal/admin/costs
GET  /internal/admin/kafka-lag
GET  /internal/admin/api-keys
```

---

## 23. Backend Services

```text
backend/
  app/
    main.py
    config.py

    api/
      routes_health.py
      routes_auth.py
      routes_chat.py
      routes_events.py
      routes_companies.py
      routes_watchlist.py
      routes_signals.py
      routes_thesis.py
      routes_admin.py

    services/
      llm_router.py
      groq_key_manager.py
      local_llm_service.py
      cache_service.py
      semantic_cache_service.py
      rag_service.py
      citation_service.py
      compliance_service.py
      audit_service.py
      rate_limit_service.py
      market_data_service.py
      signal_scoring_service.py
      thesis_service.py
      websocket_service.py

    agents/
      ingestion_agent.py
      deduplication_agent.py
      relevance_agent.py
      event_classifier_agent.py
      financial_impact_agent.py
      citation_agent.py
      compliance_guardrail_agent.py
      alert_agent.py
      bullish_bearish_ranking_agent.py
      chat_router_agent.py

    db/
      models.py
      schemas.py
      session.py
      migrations/

    workers/
      ingest_worker.py
      parse_worker.py
      classify_worker.py
      embed_worker.py
      alert_worker.py
      signal_rank_worker.py
      thesis_worker.py
      eval_worker.py

    evals/
      deepeval_tests.py
      ragas_tests.py
      promptfoo_tests.yaml

    utils/
      hashing.py
      logging.py
      time.py
      text_cleaning.py
      retry.py
```

---

## 24. Frontend Structure

Since v1 uses HTML + CSS + JavaScript:

```text
frontend/
  index.html
  dashboard.html
  company.html
  watchlist.html
  chat.html
  bullish.html
  bearish.html
  thesis.html
  market-map.html
  audit.html
  admin.html

  assets/
    css/
      style.css
      dashboard.css
      company.css
      chat.css
      signals.css
      market-map.css
      animations.css

    js/
      api.js
      auth.js
      dashboard.js
      company.js
      chat.js
      bullish.js
      bearish.js
      thesis.js
      market-map.js
      three-scene.js
      websocket.js
      admin.js

    images/
    icons/
    models/
```

---

## 25. Complete Project Structure

```text
bharat-market-intelligence-agent/
│
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Makefile
│
├── docs/
│   ├── architecture.md
│   ├── data-sources.md
│   ├── database-schema.md
│   ├── api-design.md
│   ├── agent-design.md
│   ├── chatbot-fallback-design.md
│   ├── bullish-bearish-ranking.md
│   ├── compliance.md
│   ├── scaling-plan.md
│   ├── deployment.md
│   ├── eval-report.md
│   └── demo-script.md
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── company.html
│   ├── watchlist.html
│   ├── chat.html
│   ├── bullish.html
│   ├── bearish.html
│   ├── thesis.html
│   ├── market-map.html
│   ├── audit.html
│   ├── admin.html
│   └── assets/
│       ├── css/
│       │   ├── style.css
│       │   ├── dashboard.css
│       │   ├── company.css
│       │   ├── chat.css
│       │   ├── signals.css
│       │   ├── market-map.css
│       │   └── animations.css
│       ├── js/
│       │   ├── api.js
│       │   ├── auth.js
│       │   ├── dashboard.js
│       │   ├── company.js
│       │   ├── chat.js
│       │   ├── bullish.js
│       │   ├── bearish.js
│       │   ├── thesis.js
│       │   ├── market-map.js
│       │   ├── three-scene.js
│       │   ├── websocket.js
│       │   └── admin.js
│       ├── images/
│       ├── icons/
│       └── models/
│
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── db/
│   │   ├── workers/
│   │   ├── evals/
│   │   └── utils/
│   └── tests/
│       ├── test_api.py
│       ├── test_chatbot.py
│       ├── test_rag.py
│       ├── test_compliance.py
│       └── test_signal_scoring.py
│
├── pipelines/
│   ├── airflow/
│   │   ├── dags/
│   │   │   ├── ingest_bse_announcements.py
│   │   │   ├── ingest_news.py
│   │   │   ├── process_documents.py
│   │   │   ├── generate_daily_market_summary.py
│   │   │   └── rank_bullish_bearish_signals.py
│   │   └── plugins/
│   └── dagster/
│
├── database/
│   ├── migrations/
│   ├── schema.sql
│   ├── seed_companies.sql
│   ├── indexes.sql
│   └── sample_data/
│
├── infra/
│   ├── docker/
│   ├── k8s/
│   │   ├── backend-deployment.yaml
│   │   ├── worker-deployment.yaml
│   │   ├── redis-deployment.yaml
│   │   ├── ingress.yaml
│   │   └── secrets.example.yaml
│   ├── helm/
│   └── terraform/
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   │   └── dashboards/
│   ├── langfuse/
│   └── evidently/
│
├── evals/
│   ├── datasets/
│   │   ├── rag_goldens.json
│   │   ├── financial_advice_guardrails.json
│   │   ├── prompt_injection_tests.json
│   │   └── citation_tests.json
│   ├── deepeval/
│   ├── ragas/
│   └── promptfoo/
│       └── promptfooconfig.yaml
│
├── scripts/
│   ├── setup_local.sh
│   ├── run_backend.sh
│   ├── run_workers.sh
│   ├── run_evals.sh
│   ├── seed_database.py
│   ├── ingest_sample_data.py
│   └── generate_demo_data.py
│
└── .github/
    └── workflows/
        ├── ci.yml
        ├── evals.yml
        ├── docker-build.yml
        └── deploy.yml
```

---

## 26. 3D UI Plan

### Landing Animation

- Rotating India network
- Market nodes pulsing
- Sector clusters glowing
- News/event particles flowing into dashboard

### Market Map

- Sectors as clusters
- Companies as nodes
- Node size = event volume or market cap
- Node color = bullish/bearish/neutral signal
- Pulse animation = fresh event
- Click = company page

### Dashboard Animation

- Live event ticker
- Risk radar
- Sector heatmap
- Floating alert cards
- Glassmorphism panels

Keep animations lightweight so the app remains fast.

---

## 27. Reliability Strategy

The system must be designed for failure.

### 27.1 If LLM Fails

Return:

- Source snippets
- Event tables
- Template answers
- Cached summaries

### 27.2 If Vector Search Fails

Fallback:

- Keyword search
- SQL search
- Recent event search

### 27.3 If News Source Fails

Continue:

- BSE/NSE ingestion
- Existing cached news
- Other sources

### 27.4 If Groq Key Fails

Fallback:

- Next Groq key
- Local model
- Template answer
- Source-only answer

### 27.5 If Database Is Slow

Use:

- Redis cache
- Precomputed summaries
- Read replicas later
- Pagination
- Materialized views

### 27.6 If Worker Fails

Use:

- Retry queue
- Dead-letter queue
- Worker health checks
- Restart policy

---

## 28. Observability Metrics

Track:

- API latency
- Chat latency
- LLM latency
- LLM error rate
- LLM token usage
- API key usage
- Cost estimate
- Cache hit ratio
- Semantic cache hit ratio
- Kafka lag
- Worker failure rate
- Ingestion freshness
- Documents processed per minute
- Events classified per minute
- Citation coverage
- RAG faithfulness
- Hallucination score
- Prompt injection pass rate
- Database slow queries
- WebSocket connection count

---

## 29. Evaluation Plan

### 29.1 DeepEval

Use for:

- Answer relevancy
- Faithfulness
- Hallucination
- Contextual precision
- Contextual recall

### 29.2 RAGAS

Use for:

- Retrieval quality
- Faithfulness
- Answer correctness
- Context utilization

### 29.3 Promptfoo

Use for:

- Prompt regression
- Prompt injection
- Jailbreak attempts
- Unsafe financial advice tests
- Refusal correctness

---

## 30. CI/CD Plan

GitHub Actions should run:

```text
Lint
Unit tests
API tests
Compliance tests
RAG tests
DeepEval tests
Promptfoo tests
Docker build
Security scan
Deploy
```

Deployment should fail if:

- Faithfulness score below threshold
- Prompt injection tests fail
- Financial advice guardrail fails
- API tests fail
- Docker build fails

---

## 31. Deployment Plan

### 31.1 Local Development

```text
Docker Compose
FastAPI
Redpanda
Redis
Supabase/Postgres
Langfuse
Airflow
Frontend static server
```

### 31.2 Public Demo

```text
Frontend: Vercel
Backend: Render / Railway / Fly.io
Database: Supabase
Cache: Upstash Redis
Workers: Background service
```

### 31.3 Production-Like Demo

```text
Kubernetes using k3d/kind
Ingress
Backend pods
Worker pods
Redis
Redpanda
Prometheus
Grafana
Langfuse
```

---

## 32. Scalability Plan

### Stage 1: Local MVP

Users: 1 to 10

Goal:

- Prove ingestion
- Prove RAG
- Prove chatbot
- Prove dashboard

### Stage 2: Public Portfolio Demo

Users: 100 to 1,000/month

Goal:

- Stable public demo
- Cached answers
- Limited chatbot
- Watchlist support

### Stage 3: 10k Users

Needs:

- Kubernetes
- Managed Postgres
- Managed Redis
- Kafka/Redpanda
- CDN
- Worker autoscaling
- API gateway

### Stage 4: 100k to 1M Users

Needs:

- Read replicas
- Partitioned DB
- Qdrant vector cluster
- Kafka partitioning
- Separate ingestion and inference clusters
- Multi-layer cache
- Queue-based deep research

### Stage 5: 10M Users

Needs paid infrastructure:

- Multi-region Kubernetes
- Managed Kafka
- Distributed database
- Global CDN
- Dedicated inference gateway
- Strict quotas
- Licensed market data
- SRE monitoring
- Incident response

---

## 33. Latency Targets

Do not claim zero latency.

Use realistic targets:

```text
Dashboard load: < 1.5 seconds
Cached chatbot answer: < 500 ms
SQL/template answer: < 1 second
RAG answer: 2 to 5 seconds
Deep research answer: 10 to 30 seconds
Alert generation: < 30 seconds in MVP
WebSocket dashboard update: 1 to 5 seconds
```

---

## 34. MVP Build Order

### Phase 1: Foundation

- Create repo
- Setup frontend pages
- Setup FastAPI
- Setup Supabase schema
- Setup Redis
- Setup Docker Compose
- Add company master table

### Phase 2: Data Ingestion

- Ingest sample company announcements
- Ingest sample news
- Store raw documents
- Chunk documents
- Generate embeddings
- Store in pgvector

### Phase 3: Market Events

- Classify events
- Store market_events
- Add citations
- Build dashboard API
- Show latest events

### Phase 4: Chatbot

- Add chat UI
- Add SQL/template answers
- Add RAG answers
- Add Groq router
- Add local fallback
- Add semantic cache

### Phase 5: Bullish/Bearish Watchlists

- Build scoring service
- Generate top 10 bullish candidates
- Generate top 10 bearish risk candidates
- Add thesis pages
- Add citations and disclaimers

### Phase 6: Observability

- Add Langfuse
- Add audit logs
- Add Prometheus metrics
- Add Grafana dashboard

### Phase 7: Evaluation

- Add DeepEval
- Add RAGAS
- Add Promptfoo
- Add CI/CD eval gate

### Phase 8: Streaming

- Add Redpanda
- Add worker topics
- Add dead-letter queue
- Add async processing

### Phase 9: Deployment

- Deploy frontend to Vercel
- Deploy backend
- Add environment variables
- Add GitHub Actions
- Add public demo data

### Phase 10: Kubernetes

- Create k8s manifests
- Deploy locally on k3d/kind
- Add autoscaling simulation
- Add architecture documentation

---

## 35. Demo Script for Recruiters

1. Open landing page.
2. Show live dashboard.
3. Click latest negative event.
4. Show citation and source.
5. Ask chatbot: “What happened with this company this week?”
6. Show source-grounded answer.
7. Open bullish watchlist.
8. Click a company and show bullish thesis + risks.
9. Open bearish risk watchlist.
10. Click a company and show risk thesis + counterpoints.
11. Show audit page.
12. Show Langfuse traces.
13. Show eval report.
14. Show Docker/Kubernetes architecture.
15. Explain fallback chatbot without API keys.

---

## 36. Resume Bullet After Building

```text
Built Bharat Market Intelligence Agent, a real-time Indian financial intelligence platform using FastAPI, Supabase Postgres, pgvector, Redis, Redpanda/Kafka, LangGraph agents, Groq LLM routing, local LLM fallback, DeepEval/RAGAS evaluation, Langfuse tracing, and Kubernetes-ready deployment; generated source-cited market event summaries, bullish/bearish signal watchlists, and compliance-safe chatbot answers with audit logs.
```

---

## 37. Final Goal

This project should prove that you can build:

- AI systems
- Data pipelines
- Real-time event processing
- Financial intelligence products
- Scalable backend systems
- LLM evaluation workflows
- LLM observability
- Safe and compliant AI assistants
- Production-ready architecture

This is not just a portfolio app.

This is a complete AI + FinTech + Data Engineering + MLOps + Systems Design project.
