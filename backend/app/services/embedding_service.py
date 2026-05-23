"""
Bharat Market Intelligence Agent — Embedding Service

Generates vector embeddings for document chunks.
Supports local sentence-transformers (default) and OpenAI embeddings.

Local-first design: works without any API key using MiniLM.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()

# Global model reference (lazy loaded)
_local_model = None


def _get_local_model():
    """Lazy-load the local sentence-transformer model."""
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = settings.embedding_model
            logger.info("Loading embedding model: %s", model_name)
            _local_model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error("Failed to load embedding model: %s", str(e))
            raise
    return _local_model


def generate_embeddings_local(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using local sentence-transformer model.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (dimension depends on model)
    """
    if not texts:
        return []

    model = _get_local_model()
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,
        batch_size=32,
    )

    return embeddings.tolist()


async def generate_embeddings_openai(
    texts: list[str],
    model: str = "text-embedding-ada-002",
) -> list[list[float]]:
    """
    Generate embeddings using OpenAI API.

    Args:
        texts: List of text strings to embed
        model: OpenAI embedding model name

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    if not settings.openai_api_key:
        logger.error("OpenAI API key not configured")
        raise ValueError("OpenAI API key required for OpenAI embeddings")

    import httpx

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    # Process in batches of 100 (OpenAI limit is 2048)
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers=headers,
                json={
                    "input": batch,
                    "model": model,
                },
            )
            response.raise_for_status()
            data = response.json()

            batch_embeddings = [
                item["embedding"] for item in data["data"]
            ]
            all_embeddings.extend(batch_embeddings)

    return all_embeddings


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using the configured provider.
    Falls back to local model if OpenAI fails.
    """
    if settings.embedding_provider == "openai" and settings.openai_api_key:
        try:
            return await generate_embeddings_openai(texts)
        except Exception as e:
            logger.warning(
                "OpenAI embedding failed, falling back to local: %s", str(e)
            )

    return generate_embeddings_local(texts)


async def embed_unprocessed_chunks(
    db: AsyncSession,
    batch_size: int = 100,
    max_chunks: int = 1000,
) -> int:
    """
    Find document chunks without embeddings and generate them.

    Args:
        db: Database session
        batch_size: Number of chunks to embed at once
        max_chunks: Maximum total chunks to process in one run

    Returns:
        Number of chunks embedded
    """
    # Find chunks without embeddings
    query = (
        select(DocumentChunk)
        .where(DocumentChunk.embedding.is_(None))
        .limit(max_chunks)
    )
    result = await db.execute(query)
    chunks = result.scalars().all()

    if not chunks:
        logger.info("No unprocessed chunks found")
        return 0

    logger.info("Found %d chunks to embed", len(chunks))
    total_embedded = 0

    # Process in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.chunk_text for c in batch]

        try:
            embeddings = await generate_embeddings(texts)

            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

            await db.flush()
            total_embedded += len(batch)

            logger.info(
                "Embedded batch %d-%d (%d/%d)",
                i, i + len(batch), total_embedded, len(chunks)
            )

        except Exception as e:
            logger.error(
                "Embedding batch %d failed: %s", i, str(e)
            )
            continue

    await db.commit()
    logger.info("Total chunks embedded: %d", total_embedded)
    return total_embedded
