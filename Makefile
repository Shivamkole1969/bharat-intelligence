# ============================================================
# Bharat Market Intelligence Agent — Makefile
# ============================================================

.PHONY: help dev up down logs db-init db-seed ingest classify signals eval test lint clean

# ── Help ─────────────────────────────────────────────────────
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Development ──────────────────────────────────────────────
dev: ## Run backend in development mode
	cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-worker: ## Run background scheduler in development
	cd backend && python -m app.workers.scheduler

frontend: ## Serve frontend with Python HTTP server
	cd frontend && python -m http.server 5500

# ── Docker ───────────────────────────────────────────────────
up: ## Start full stack with Docker Compose
	docker compose up -d

up-build: ## Build and start full stack
	docker compose up -d --build

down: ## Stop all services
	docker compose down

down-clean: ## Stop all services and remove volumes
	docker compose down -v

logs: ## Follow all container logs
	docker compose logs -f

logs-backend: ## Follow backend logs
	docker compose logs -f backend

logs-worker: ## Follow worker logs
	docker compose logs -f worker

ps: ## Show running containers
	docker compose ps

# ── Database ─────────────────────────────────────────────────
db-init: ## Initialize database (create tables + seed)
	cd backend && python -c "import asyncio; from scripts.init_database import main; asyncio.run(main())"

db-seed: ## Seed Nifty 500 companies
	cd backend && python -c "import asyncio; from scripts.seed_database import seed_companies; asyncio.run(seed_companies())"

db-shell: ## Open psql shell
	docker compose exec postgres psql -U postgres -d bharat_market_intel

# ── Data Pipeline ────────────────────────────────────────────
ingest: ## Trigger full ingestion pipeline (NSE + BSE + News)
	curl -s -X POST http://127.0.0.1:8000/api/admin/ingest/trigger | python -m json.tool

ingest-exchange: ## Trigger exchange-only ingestion (NSE + BSE Level 1)
	curl -s -X POST "http://127.0.0.1:8000/api/admin/ingest/trigger?fetch_news=false" | python -m json.tool

ingest-news: ## Trigger news-only ingestion (Level 3-4)
	curl -s -X POST "http://127.0.0.1:8000/api/admin/ingest/trigger?fetch_nse=false&fetch_bse=false" | python -m json.tool

classify: ## Classify unprocessed documents into events
	curl -s -X POST http://127.0.0.1:8000/api/admin/classify/batch | python -m json.tool

signals: ## Recompute signal scores for all companies
	@echo "Signal scoring triggered via background worker"

stats: ## Get system statistics
	curl -s http://127.0.0.1:8000/api/admin/stats | python -m json.tool

# ── Evaluation ───────────────────────────────────────────────
eval: ## Run full evaluation suite
	curl -s -X POST http://127.0.0.1:8000/api/admin/eval/run | python -m json.tool

eval-history: ## Show evaluation history
	curl -s http://127.0.0.1:8000/api/admin/eval/history | python -m json.tool

# ── Observability ────────────────────────────────────────────
health: ## Quick health check
	curl -s http://127.0.0.1:8000/api/health | python -m json.tool

health-deep: ## Deep health check (all subsystems)
	curl -s http://127.0.0.1:8000/api/health/deep | python -m json.tool

metrics: ## Show Prometheus metrics
	curl -s http://127.0.0.1:8000/api/metrics

audit-verify: ## Verify audit log hash chain integrity
	curl -s http://127.0.0.1:8000/api/audit/verify | python -m json.tool

audit-logs: ## Show recent audit log entries
	curl -s http://127.0.0.1:8000/api/audit/logs?limit=20 | python -m json.tool

# ── Testing ──────────────────────────────────────────────────
test: ## Run tests
	cd backend && python -m pytest tests/ -v --tb=short

lint: ## Run linter
	cd backend && ruff check app/ --fix

format: ## Format code
	cd backend && ruff format app/

# ── Cleanup ──────────────────────────────────────────────────
clean: ## Clean Python caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
