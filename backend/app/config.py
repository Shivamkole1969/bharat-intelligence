"""
Bharat Market Intelligence Agent — Application Configuration

Loads settings from environment variables with validation.
Uses pydantic-settings for type-safe configuration.
"""

from __future__ import annotations

import logging
import os
import secrets
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "bharat-market-intelligence"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bharat_market_intel"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/bharat_market_intel"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Auto-convert postgres:// to postgresql+asyncpg:// for cloud providers."""
        if v and v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v and v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Groq LLM ---
    groq_api_keys: str = ""  # Comma-separated key:alias pairs
    groq_default_model: str = "llama-3.3-70b-versatile"
    groq_fast_model: str = "llama-3.1-8b-instant"
    groq_rpm_limit: int = 30
    groq_tpm_limit: int = 6000
    groq_daily_token_limit: int = 500000

    # --- Local LLM Fallback ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # --- Embeddings ---
    embedding_provider: str = "local"  # "openai" or "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    openai_api_key: Optional[str] = None

    # --- Supabase Auth ---
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # --- Kafka / Redpanda ---
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_group_id: str = "bharat-intel-workers"

    # --- Langfuse ---
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://localhost:3000"

    # --- Rate Limits ---
    anon_daily_chat_limit: int = 5
    free_daily_chat_limit: int = 20
    free_daily_deep_research_limit: int = 5
    max_watchlist_companies: int = 10

    # --- CORS ---
    cors_origins: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:5500"

    # --- Server ---
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1

    # --- JWT Secret ---
    # Resolved securely: env → file → ephemeral random (logged warning)
    jwt_secret_key: Optional[str] = None

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    def get_cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def get_groq_keys(self) -> list[dict]:
        """Parse Groq API keys from comma-separated key:alias format."""
        if not self.groq_api_keys:
            return []
        keys = []
        for entry in self.groq_api_keys.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":", 1)
            if len(parts) == 2:
                keys.append({"key": parts[0], "alias": parts[1]})
            else:
                keys.append({"key": parts[0], "alias": f"key_{len(keys)}"})
        return keys

    def resolve_jwt_secret(self) -> str:
        """
        Resolve JWT secret with secure multi-tiered fallback:
        1. Environment variable (jwt_secret_key)
        2. Local file (jwt_secret.txt)
        3. Ephemeral random generation (logged warning — instance-isolated)
        """
        if self.jwt_secret_key:
            return self.jwt_secret_key

        secret_file = "jwt_secret.txt"
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                secret = f.read().strip()
                if secret:
                    return secret

        logger.warning(
            "JWT_SECRET_KEY not found in environment or file. "
            "Generating ephemeral secret. This instance is isolated — "
            "sessions will not persist across restarts or scale horizontally."
        )
        return secrets.token_hex(32)

    @property
    def groq_api_key(self) -> Optional[str]:
        """Get the first available Groq API key."""
        keys = self.get_groq_keys()
        return keys[0]["key"] if keys else None

    @property
    def ollama_url(self) -> str:
        """Alias for ollama_base_url."""
        return self.ollama_base_url

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
