# Bharat Market Intelligence Agent — AI Context

> **Token-saving rules**: Skip re-reading completed phases. Focus only on active work.

## Stack (One-liner)
FastAPI + Vanilla HTML/CSS/JS + Postgres/pgvector + Redis + Groq LLM + Groww/NSE OHLCV

## Active Architecture

```
frontend/          → Static HTML+JS (served by nginx:3000)
backend/app/       → FastAPI (Docker:8000)
  api/             → routes_*.py (health, companies, events, signals, chat, candlestick)
  services/        → ohlcv_fetcher.py, candlestick_patterns.py, llm_router.py, rag_service.py
  db/              → models.py (19 tables), schemas.py, session.py
database/          → schema.sql, seed_companies.sql (Nifty 500)
```

## Key Files (Edit Frequently)
| File | Purpose |
|------|---------|
| `frontend/assets/js/company.js` | Company page: TradingView + prediction meter + AI section |
| `frontend/assets/js/candlestick.js` | Canvas chart: zoom/pan, projected candles, patterns |
| `frontend/assets/js/api.js` | Centralized API client (BharatAPI global) |
| `frontend/assets/js/apikeys.js` | User API key management (GROQ/OpenAI/etc) |
| `frontend/assets/css/style.css` | Master stylesheet (1500+ lines) |
| `backend/app/api/routes_candlestick.py` | Candlestick analysis endpoint |
| `backend/app/api/routes_chat.py` | 8-layer chat pipeline |
| `backend/app/services/ohlcv_fetcher.py` | Multi-source OHLCV: Groww → NSE → Yahoo |
| `backend/app/services/candlestick_patterns.py` | Nison pattern engine (15+ patterns) |
| `backend/app/db/schemas.py` | Pydantic request/response models |

## Data Flow
```
User searches ticker → company.html?symbol=XYZ
  → TradingView widgets (BSE:XYZ via Blob URLs for & safety)
  → /api/candlestick/XYZ → Groww API → pattern engine → prediction
  → Prediction Meter (gauge canvas) + Candlestick Chart (zoom/pan canvas)
  → /api/signals/thesis/XYZ → AI conviction score
  → /api/events/company/XYZ → latest market events
```

## OHLCV Source Priority
1. **Groww** (charting API, timestamps in SECONDS not ms)
2. **NSE India** (official, needs cookie preflight)
3. **Yahoo Finance** (yfinance, rate-limited)

## Rules (Always Follow)
- **Compliance**: No buy/sell/short. Label as "Bullish Watchlist" / "Bearish Risk". Always add SEBI disclaimer.
- **Security**: textContent over innerHTML, parameterized SQL, no secrets in code, CSP headers
- **Frontend**: Dark theme (#060a13), glassmorphism, Inter/system fonts, responsive
- **Backend**: async/await, type hints, snake_case, structured logging
- **Docker**: `docker compose up -d --build backend` to rebuild. Frontend auto-serves via nginx volume mount.
- **Cache busting**: Bump `?v=N` on CSS/JS links after changes
- **Special chars**: Symbols like M&M need Blob URLs for TradingView srcdoc (not innerHTML srcdoc)

## Current State
- All 10 build phases COMPLETE ✅
- Company page: header, prediction meter, TradingView, candlestick chart, AI intelligence, news
- API key management: 🔑 button in nav, supports GROQ/OpenAI/Anthropic/Gemini
- Candlestick chart: Zoom/pan, projected candles with glow, proper date labels
- Pending: News sentiment integration for AI Intelligence section

## Database (19 Tables)
companies, data_sources, raw_documents, document_chunks, market_events, event_citations, users, watchlists, watchlist_companies, chat_sessions, chat_messages, llm_api_keys, api_key_usage, audit_logs, eval_runs, system_health, stock_signal_scores, stock_theses, semantic_cache

## API Endpoints
GET /api/health, /api/companies, /api/companies/{symbol}, /api/events/latest, /api/events/company/{symbol}, /api/market/summary, /api/signals/bullish/top, /api/signals/bearish/top, /api/signals/thesis/{symbol}, /api/candlestick/{symbol}
POST /api/chat (accepts user_api_config for custom LLM keys)
