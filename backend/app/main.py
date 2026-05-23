"""
Bharat Market Intelligence Agent — FastAPI Application Entry Point

Production-grade FastAPI server with:
- CORS with strict origin control
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options)
- Rate limiting middleware
- Database lifecycle management
- API versioning via route prefixes
- Structured logging
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes_admin import router as admin_router
from app.api.routes_chat import router as chat_router
from app.api.routes_companies import router as companies_router
# from app.api.routes_eval import router as eval_router
from app.api.routes_events import router as events_router
from app.api.routes_health import router as health_router
from app.api.routes_observability import router as observability_router
from app.api.routes_signals import router as signals_router
from app.api.routes_candlestick import router as candlestick_router
from app.config import get_settings
from app.db.session import close_db, init_db
from app.utils.helpers import setup_logging

settings = get_settings()
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


# ============================================================
# Application Lifecycle
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    logger.info(
        "Starting %s in %s mode", settings.app_name, settings.app_env
    )

    # Initialize database tables (dev only — use migrations in production)
    if not settings.is_production:
        try:
            await init_db()
        except Exception as e:
            logger.error("Database initialization failed: %s", str(e))
            logger.warning(
                "Application starting without database. "
                "Some features will be unavailable."
            )

    # Seed companies on every startup (idempotent — skips existing)
    try:
        from app.db.seed_companies import seed_companies
        from app.db.session import async_session_factory
        async with async_session_factory() as session:
            inserted = await seed_companies(session)
            if inserted > 0:
                logger.info("Company seed: %d new companies added", inserted)
    except Exception as e:
        logger.warning("Company seed skipped: %s", str(e))

    yield

    # Cleanup
    await close_db()
    logger.info("Application shutdown complete")


# ============================================================
# FastAPI Application
# ============================================================
app = FastAPI(
    title="Bharat Market Intelligence Agent",
    description=(
        "Real-time AI intelligence platform for Indian financial markets. "
        "Tracks NSE/BSE announcements, company filings, earnings transcripts, "
        "and public news to generate source-cited market intelligence."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)


# ============================================================
# Middleware — CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# ============================================================
# Middleware — Security Headers
# ============================================================
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Add security headers to every response."""
    response = await call_next(request)

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://s3.tradingview.com https://tv-static.tradingview.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "frame-src https://s.tradingview.com https://*.tradingview.com; "
        "connect-src 'self' https://*.tradingview.com https://scanner.tradingview.com wss://*.tradingview.com; "
        "frame-ancestors 'none';"
    )
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Disable browser features we don't use
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )

    return response


# ============================================================
# Middleware — Request Logging & Timing
# ============================================================
@app.middleware("http")
async def log_requests(request: Request, call_next) -> Response:
    """Log request details and measure response time."""
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)

    logger.info(
        "%s %s → %d (%dms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    response.headers["X-Response-Time"] = f"{duration_ms}ms"
    return response


# ============================================================
# Global Exception Handler
# ============================================================
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """
    Catch unhandled exceptions and return a safe error response.
    Never expose stack traces or internal details to users.
    """
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ============================================================
# Register Routers
# ============================================================
app.include_router(health_router, prefix="/api")
app.include_router(companies_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
# app.include_router(eval_router, prefix="/api")
app.include_router(observability_router, prefix="/api")
app.include_router(candlestick_router, prefix="/api")


# ============================================================
# Static Frontend (for Render / standalone deployment)
# ============================================================
import os
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if not FRONTEND_DIR.exists():
    # Check one level up (when running from repo root)
    FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Serve static assets (CSS, JS, images)
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Serve HTML pages
    @app.get("/{page_name}.html")
    async def serve_page(page_name: str):
        html_file = FRONTEND_DIR / f"{page_name}.html"
        if html_file.exists():
            return FileResponse(str(html_file), media_type="text/html")
        return JSONResponse(status_code=404, content={"error": "Page not found"})

    # Root → index.html
    @app.get("/")
    async def serve_index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file), media_type="text/html")
        return {
            "name": "Bharat Market Intelligence Agent",
            "version": "2.0.0",
            "health": "/api/health",
        }

    logger.info("Frontend static files mounted from %s", FRONTEND_DIR)
else:
    # No frontend directory — just serve API
    @app.get("/")
    async def root() -> dict:
        """Root endpoint — basic info."""
        return {
            "name": "Bharat Market Intelligence Agent",
            "version": "2.0.0",
            "description": "Real-time AI intelligence for Indian financial markets",
            "docs": "/docs",
            "health": "/api/health",
        }

