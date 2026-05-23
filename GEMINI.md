# Bharat Market Intelligence — Gemini Context

## Token Efficiency Rules
- **DO NOT** re-read completed phases or build history
- **DO NOT** explain what you're about to do — just do it
- **PREFER** single file edits over multiple small changes
- **USE** `docker compose up -d --build backend` after Python changes
- **SKIP** frontend rebuild — nginx serves files directly from volume mount
- When fixing bugs, check `docker logs bharat-backend --tail 30` first

## Quick Reference
- **Backend**: FastAPI at localhost:8000, Docker container `bharat-backend`
- **Frontend**: nginx at localhost:3000, static files in `frontend/`
- **DB**: Postgres+pgvector at localhost:5432, db=`bharat_intelligence`
- **Redis**: localhost:6379
- **OHLCV**: Groww API (timestamps in SECONDS, not ms!) → NSE India → Yahoo Finance
- **TradingView**: Use Blob URLs for symbols with `&` (e.g., M&M)
- **CSS cache**: Bump `?v=N` query param after style changes

## File Map (Most Edited)
```
frontend/assets/js/company.js      — Company page logic
frontend/assets/js/candlestick.js  — Interactive canvas chart
frontend/assets/js/api.js          — API client (BharatAPI global)
frontend/assets/css/style.css      — Master styles
backend/app/api/routes_candlestick.py — Candlestick endpoint
backend/app/api/routes_chat.py     — Chat pipeline
backend/app/services/ohlcv_fetcher.py — OHLCV data fetching
backend/app/db/schemas.py          — Pydantic models
```

## Conventions
- Dark theme: bg=#060a13, green=#22c55e, red=#ef4444, amber=#f59e0b
- Python: async/await, type hints, snake_case
- JS: IIFE modules, BharatAPI global, camelCase
- No buy/sell advice. Always add SEBI disclaimer.
