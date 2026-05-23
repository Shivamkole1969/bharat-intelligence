"""
Bharat Market Intelligence Agent — Document Processing Service

Handles:
1. Text chunking for RAG pipeline
2. Company entity extraction from documents
3. Document-to-company mapping
4. Chunk metadata enrichment
"""

from __future__ import annotations

import logging
import re
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, DocumentChunk, RawDocument
from app.utils.helpers import clean_text

logger = logging.getLogger(__name__)

# Chunking parameters
DEFAULT_CHUNK_SIZE = 512  # tokens (approximate)
DEFAULT_CHUNK_OVERLAP = 64  # tokens overlap between chunks
CHARS_PER_TOKEN = 4  # rough approximation


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """
    Split text into overlapping chunks for embedding.

    Uses sentence-aware splitting to avoid breaking mid-sentence.
    Each chunk contains metadata about its position.

    Args:
        text: Raw text to chunk
        chunk_size: Target chunk size in approximate tokens
        chunk_overlap: Overlap between chunks in approximate tokens

    Returns:
        List of chunk dicts with text, index, and token_count
    """
    if not text or not text.strip():
        return []

    text = clean_text(text)
    max_chars = chunk_size * CHARS_PER_TOKEN
    overlap_chars = chunk_overlap * CHARS_PER_TOKEN

    # Split into sentences
    sentences = _split_sentences(text)

    chunks = []
    current_chunk: list[str] = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # If single sentence exceeds max, split it by words
        if sentence_len > max_chars:
            if current_chunk:
                chunk_text_str = " ".join(current_chunk)
                chunks.append(chunk_text_str)
                current_chunk = []
                current_length = 0

            # Split long sentence into word-level chunks
            words = sentence.split()
            word_chunk: list[str] = []
            word_length = 0
            for word in words:
                if word_length + len(word) + 1 > max_chars and word_chunk:
                    chunks.append(" ".join(word_chunk))
                    # Keep overlap
                    overlap_words = word_chunk[-(overlap_chars // 6):]
                    word_chunk = overlap_words
                    word_length = sum(len(w) + 1 for w in word_chunk)
                word_chunk.append(word)
                word_length += len(word) + 1
            if word_chunk:
                chunks.append(" ".join(word_chunk))
            continue

        # Check if adding this sentence exceeds chunk size
        if current_length + sentence_len + 1 > max_chars and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunks.append(chunk_text_str)

            # Keep overlap sentences
            overlap_length = 0
            overlap_start = len(current_chunk)
            for i in range(len(current_chunk) - 1, -1, -1):
                overlap_length += len(current_chunk[i]) + 1
                if overlap_length >= overlap_chars:
                    overlap_start = i
                    break

            current_chunk = current_chunk[overlap_start:]
            current_length = sum(len(s) + 1 for s in current_chunk)

        current_chunk.append(sentence)
        current_length += sentence_len + 1

    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    # Build result with metadata
    result = []
    for idx, chunk in enumerate(chunks):
        token_count = len(chunk) // CHARS_PER_TOKEN
        result.append({
            "chunk_index": idx,
            "chunk_text": chunk,
            "token_count": token_count,
        })

    return result


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex-based heuristics."""
    # Pattern for sentence boundaries
    # Handles: periods, exclamation, question marks followed by space and capital
    # Avoids splitting on abbreviations like Mr., Dr., Rs., etc.
    abbreviations = r"(?<!\bMr)(?<!\bMrs)(?<!\bDr)(?<!\bRs)(?<!\bCr)(?<!\bLt)(?<!\bSt)(?<!\bNo)"
    pattern = rf"{abbreviations}[.!?]+\s+"

    sentences = re.split(pattern, text)
    return [s.strip() for s in sentences if s.strip()]


async def map_document_to_company(
    document: dict[str, Any],
    db: AsyncSession,
) -> Optional[UUID]:
    """
    Map a document to a company using BSE code, NSE symbol, or name matching.

    Args:
        document: Normalized document dict
        db: Database session

    Returns:
        Company UUID if matched, None otherwise
    """
    metadata = document.get("metadata", {})

    # Try BSE code match
    bse_code = metadata.get("bse_scrip_code") or document.get("bse_code")
    if bse_code:
        query = select(Company).where(Company.bse_code == str(bse_code))
        result = await db.execute(query)
        company = result.scalar_one_or_none()
        if company:
            return company.id

    # Try direct NSE symbol match (fastest path for exchange filings)
    nse_symbol = document.get("nse_symbol") or metadata.get("symbol")
    if nse_symbol:
        query = select(Company).where(
            (Company.symbol == nse_symbol) | (Company.nse_symbol == nse_symbol)
        )
        result = await db.execute(query)
        company = result.scalar_one_or_none()
        if company:
            return company.id

    # Try NSE symbol match from title
    title = document.get("title", "")
    company_name = document.get("company_name", "")

    # Extract symbol patterns from title (e.g., "TCS", "INFY", "RELIANCE")
    potential_symbols = re.findall(r'\b([A-Z]{2,15})\b', title)

    for symbol in potential_symbols:
        query = select(Company).where(
            (Company.symbol == symbol) | (Company.nse_symbol == symbol)
        )
        result = await db.execute(query)
        company = result.scalar_one_or_none()
        if company:
            return company.id

    # Try company name match
    if company_name:
        # Remove common suffixes for matching
        search_name = re.sub(
            r'\s+(Ltd|Limited|Corp|Corporation|Inc|Industries|Enterprises)\b',
            '',
            company_name,
            flags=re.IGNORECASE,
        ).strip()

        if len(search_name) >= 3:
            query = select(Company).where(
                Company.company_name.ilike(f"%{search_name}%")
            )
            result = await db.execute(query)
            company = result.scalar_one_or_none()
            if company:
                return company.id

    return None


async def process_and_store_document(
    document: dict[str, Any],
    db: AsyncSession,
) -> Optional[UUID]:
    """
    Process a raw document: store it, chunk it, and save chunks.

    Args:
        document: Normalized document dict from scraper/ingestion
        db: Database session

    Returns:
        RawDocument UUID if stored, None if duplicate
    """
    # Check for duplicate via content hash
    content_hash = document.get("content_hash")
    if content_hash:
        existing = await db.execute(
            select(RawDocument).where(RawDocument.content_hash == content_hash)
        )
        if existing.scalar_one_or_none():
            logger.debug("Duplicate document skipped: %s", content_hash[:16])
            return None

    # Map to company
    company_id = await map_document_to_company(document, db)

    # Store raw document
    raw_doc = RawDocument(
        company_id=company_id,
        document_type=document.get("document_type", "unknown"),
        title=document.get("title"),
        url=document.get("source_url"),
        raw_text=document.get("raw_text"),
        published_at=document.get("published_at"),
        content_hash=content_hash,
        metadata_json=document.get("metadata", {}),
    )
    db.add(raw_doc)
    await db.flush()  # Get the ID

    # Chunk the text
    raw_text = document.get("raw_text", "")
    if raw_text and len(raw_text) > 50:
        chunks = chunk_text(raw_text)

        for chunk_data in chunks:
            chunk = DocumentChunk(
                document_id=raw_doc.id,
                company_id=company_id,
                chunk_index=chunk_data["chunk_index"],
                chunk_text=chunk_data["chunk_text"],
                token_count=chunk_data["token_count"],
            )
            db.add(chunk)

        logger.info(
            "Stored document '%s' with %d chunks (company: %s)",
            (document.get("title", "")[:50]),
            len(chunks),
            company_id or "unmapped",
        )

    return raw_doc.id
