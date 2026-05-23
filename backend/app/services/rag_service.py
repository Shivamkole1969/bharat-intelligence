"""
Bharat Market Intelligence Agent — RAG (Retrieval-Augmented Generation) Service

Vector similarity search using pgvector for document retrieval.
Supports multiple search strategies:
1. Pure vector similarity (cosine distance)
2. Hybrid: vector + keyword filtering
3. Company-scoped search
4. Sector-scoped search
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, DocumentChunk, RawDocument
from app.services.embedding_service import generate_embeddings

logger = logging.getLogger(__name__)


async def vector_search(
    query: str,
    db: AsyncSession,
    top_k: int = 10,
    company_id: Optional[UUID] = None,
    sector: Optional[str] = None,
    min_similarity: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Perform vector similarity search over document chunks.

    Uses pgvector's cosine distance operator (<=>).

    Args:
        query: Natural language search query
        db: Database session
        top_k: Number of results to return
        company_id: Optional company filter
        sector: Optional sector filter
        min_similarity: Minimum cosine similarity threshold

    Returns:
        List of matching chunks with metadata and similarity scores
    """
    # Generate embedding for the query
    try:
        query_embeddings = await generate_embeddings([query])
        if not query_embeddings:
            logger.error("Failed to generate query embedding")
            return []
        query_embedding = query_embeddings[0]
    except Exception as e:
        logger.error("Embedding generation failed: %s", str(e))
        return []

    # Build the SQL query with pgvector cosine distance
    # 1 - cosine_distance = cosine_similarity
    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

    # Use parameterized query via SQLAlchemy text() with bound params
    sql_parts = [
        "SELECT",
        "  dc.id AS chunk_id,",
        "  dc.chunk_text,",
        "  dc.chunk_index,",
        "  dc.token_count,",
        "  dc.section_title,",
        "  dc.document_id,",
        "  rd.title AS document_title,",
        "  rd.url AS source_url,",
        "  rd.document_type,",
        "  rd.published_at,",
        "  c.symbol AS company_symbol,",
        "  c.company_name,",
        "  c.sector,",
        f"  1 - (dc.embedding <=> :query_vec::vector) AS similarity",
        "FROM document_chunks dc",
        "LEFT JOIN raw_documents rd ON dc.document_id = rd.id",
        "LEFT JOIN companies c ON dc.company_id = c.id",
        "WHERE dc.embedding IS NOT NULL",
    ]

    params: dict[str, Any] = {"query_vec": embedding_str}

    if company_id:
        sql_parts.append("  AND dc.company_id = :company_id")
        params["company_id"] = str(company_id)

    if sector:
        sql_parts.append("  AND c.sector = :sector")
        params["sector"] = sector

    sql_parts.append(f"  AND 1 - (dc.embedding <=> :query_vec::vector) >= :min_sim")
    params["min_sim"] = min_similarity

    sql_parts.append(f"ORDER BY dc.embedding <=> :query_vec::vector")
    sql_parts.append(f"LIMIT :top_k")
    params["top_k"] = top_k

    sql_query = "\n".join(sql_parts)

    try:
        result = await db.execute(text(sql_query), params)
        rows = result.fetchall()

        chunks = []
        for row in rows:
            chunks.append({
                "chunk_id": str(row.chunk_id),
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "token_count": row.token_count,
                "section_title": row.section_title,
                "document_id": str(row.document_id) if row.document_id else None,
                "document_title": row.document_title,
                "source_url": row.source_url,
                "document_type": row.document_type,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "company_symbol": row.company_symbol,
                "company_name": row.company_name,
                "sector": row.sector,
                "similarity": round(float(row.similarity), 4),
            })

        logger.info(
            "Vector search: query='%s' → %d results (top sim=%.3f)",
            query[:50],
            len(chunks),
            chunks[0]["similarity"] if chunks else 0,
        )

        return chunks

    except Exception as e:
        logger.error("Vector search failed: %s", str(e))
        return []


async def hybrid_search(
    query: str,
    db: AsyncSession,
    top_k: int = 10,
    company_symbol: Optional[str] = None,
    sector: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Hybrid search: combine vector similarity with keyword matching.

    Retrieves via both vector search and keyword search,
    then merges and re-ranks results.

    Args:
        query: Search query
        db: Database session
        top_k: Number of results
        company_symbol: Optional company filter (NSE symbol)
        sector: Optional sector filter

    Returns:
        Merged and ranked results
    """
    # Resolve company_id from symbol
    company_id = None
    if company_symbol:
        result = await db.execute(
            select(Company).where(
                (Company.symbol == company_symbol.upper())
                | (Company.nse_symbol == company_symbol.upper())
            )
        )
        company = result.scalar_one_or_none()
        if company:
            company_id = company.id

    # Vector search
    vector_results = await vector_search(
        query=query,
        db=db,
        top_k=top_k,
        company_id=company_id,
        sector=sector,
    )

    # Keyword search supplement
    keyword_results = await _keyword_search(
        query=query,
        db=db,
        top_k=top_k // 2,
        company_id=company_id,
    )

    # Merge: vector results first, then keyword results not already seen
    seen_ids = {r["chunk_id"] for r in vector_results}
    merged = list(vector_results)

    for kr in keyword_results:
        if kr["chunk_id"] not in seen_ids:
            merged.append(kr)
            seen_ids.add(kr["chunk_id"])

    return merged[:top_k]


async def _keyword_search(
    query: str,
    db: AsyncSession,
    top_k: int = 5,
    company_id: Optional[UUID] = None,
) -> list[dict[str, Any]]:
    """
    Keyword-based search using PostgreSQL full-text search.
    Supplements vector search for exact term matches.
    """
    # Build tsquery from query words
    words = query.split()
    if not words:
        return []

    # Use plainto_tsquery for safe query conversion
    sql_parts = [
        "SELECT",
        "  dc.id AS chunk_id,",
        "  dc.chunk_text,",
        "  dc.chunk_index,",
        "  dc.token_count,",
        "  dc.section_title,",
        "  dc.document_id,",
        "  rd.title AS document_title,",
        "  rd.url AS source_url,",
        "  rd.document_type,",
        "  rd.published_at,",
        "  c.symbol AS company_symbol,",
        "  c.company_name,",
        "  c.sector,",
        "  0.5 AS similarity",  # Fixed score for keyword matches
        "FROM document_chunks dc",
        "LEFT JOIN raw_documents rd ON dc.document_id = rd.id",
        "LEFT JOIN companies c ON dc.company_id = c.id",
        "WHERE to_tsvector('english', dc.chunk_text) @@ plainto_tsquery('english', :query)",
    ]

    params: dict[str, Any] = {"query": query}

    if company_id:
        sql_parts.append("  AND dc.company_id = :company_id")
        params["company_id"] = str(company_id)

    sql_parts.append(f"LIMIT :top_k")
    params["top_k"] = top_k

    sql_query = "\n".join(sql_parts)

    try:
        result = await db.execute(text(sql_query), params)
        rows = result.fetchall()

        return [
            {
                "chunk_id": str(row.chunk_id),
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "token_count": row.token_count,
                "section_title": row.section_title,
                "document_id": str(row.document_id) if row.document_id else None,
                "document_title": row.document_title,
                "source_url": row.source_url,
                "document_type": row.document_type,
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "company_symbol": row.company_symbol,
                "company_name": row.company_name,
                "sector": row.sector,
                "similarity": float(row.similarity),
            }
            for row in rows
        ]
    except Exception as e:
        logger.error("Keyword search failed: %s", str(e))
        return []


async def get_context_for_query(
    query: str,
    db: AsyncSession,
    company_symbol: Optional[str] = None,
    max_context_tokens: int = 3000,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Build context string for LLM from search results.

    Returns:
        Tuple of (context_string, source_citations)
    """
    results = await hybrid_search(
        query=query,
        db=db,
        top_k=8,
        company_symbol=company_symbol,
    )

    if not results:
        return "", []

    context_parts = []
    citations = []
    total_tokens = 0

    for i, chunk in enumerate(results):
        token_count = chunk.get("token_count", 100) or 100

        if total_tokens + token_count > max_context_tokens:
            break

        # Build context entry
        source_label = chunk.get("document_title") or chunk.get("document_type", "Source")
        company = chunk.get("company_symbol") or ""
        published = chunk.get("published_at") or ""

        header = f"[Source {i+1}: {source_label}"
        if company:
            header += f" | {company}"
        if published:
            header += f" | {published[:10]}"
        header += "]"

        context_parts.append(f"{header}\n{chunk['chunk_text']}")
        total_tokens += token_count

        citations.append({
            "source": source_label,
            "company": company,
            "published_at": published,
            "snippet": chunk["chunk_text"][:150],
            "url": chunk.get("source_url"),
            "similarity": chunk.get("similarity", 0),
        })

    context = "\n\n---\n\n".join(context_parts)
    return context, citations
