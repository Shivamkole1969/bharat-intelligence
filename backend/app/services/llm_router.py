"""
Bharat Market Intelligence Agent — LLM Router Service

Routes LLM requests across multiple providers with fallback chain:
1. Groq (fast, free-tier) — primary
2. OpenAI (GPT-4o-mini) — secondary
3. Ollama (local) — fallback

Features:
- API key rotation with rate limiting
- Token usage tracking
- Automatic failover
- Response streaming support (future)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# System prompt for Indian market intelligence
SYSTEM_PROMPT = """You are Bharat Market Intelligence Analyst, an AI assistant specialized in Indian financial markets.

RULES:
1. Only use information from the provided context. If context is insufficient, say so explicitly.
2. Always cite your sources using [Source N] notation matching the context.
3. NEVER provide personalized investment advice, buy/sell recommendations, target prices, or guaranteed returns.
4. Use safe labels: "Bullish Watchlist Candidate" (not "Buy"), "Bearish Risk Candidate" (not "Sell/Short").
5. Always include the disclaimer: "This is for informational purposes only. Not investment advice."
6. If asked about insider information, tips, or guaranteed returns, politely decline and explain why.
7. Be factual, concise, and cite specific data points from the context.
8. When uncertain, express uncertainty rather than fabricating information.
9. Focus on publicly available information only.
10. Reference specific dates, numbers, and sources whenever possible.

CONTEXT FROM SOURCES:
{context}
"""

NO_CONTEXT_PROMPT = """You are Bharat Market Intelligence Analyst, an AI assistant specialized in Indian financial markets.

RULES:
1. You currently have no specific source context for this query.
2. Provide general, publicly known information only.
3. NEVER provide personalized investment advice, buy/sell recommendations, target prices, or guaranteed returns.
4. Be transparent that you're responding without real-time source data.
5. Always include the disclaimer: "This is for informational purposes only. Not investment advice."
6. Suggest the user ask about specific companies or events for source-cited answers.
"""


async def call_groq(
    messages: list[dict[str, str]],
    model: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """
    Call Groq API for fast LLM inference.

    Args:
        messages: Chat messages in OpenAI format
        model: Groq model name
        max_tokens: Maximum response tokens
        temperature: Sampling temperature

    Returns:
        Response dict with answer, model, token usage
    """
    api_key = settings.groq_api_key
    if not api_key:
        raise ValueError("Groq API key not configured")

    if not model:
        model = settings.groq_default_model

    start = time.time()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        data = response.json()

    latency_ms = int((time.time() - start) * 1000)
    choice = data["choices"][0]
    usage = data.get("usage", {})

    return {
        "answer": choice["message"]["content"],
        "model": f"groq/{model}",
        "provider": "groq",
        "latency_ms": latency_ms,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "finish_reason": choice.get("finish_reason", "stop"),
    }


async def call_openai(
    messages: list[dict[str, str]],
    model: str = "gpt-4o-mini",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """Call OpenAI API."""
    api_key = settings.openai_api_key
    if not api_key:
        raise ValueError("OpenAI API key not configured")

    start = time.time()

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        data = response.json()

    latency_ms = int((time.time() - start) * 1000)
    choice = data["choices"][0]
    usage = data.get("usage", {})

    return {
        "answer": choice["message"]["content"],
        "model": f"openai/{model}",
        "provider": "openai",
        "latency_ms": latency_ms,
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        "finish_reason": choice.get("finish_reason", "stop"),
    }


async def call_ollama(
    messages: list[dict[str, str]],
    model: str = "llama3.2:3b",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> dict[str, Any]:
    """Call local Ollama instance for offline/fallback LLM."""
    ollama_url = settings.ollama_url or "http://localhost:11434"
    start = time.time()

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ollama_url}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

    latency_ms = int((time.time() - start) * 1000)

    return {
        "answer": data.get("message", {}).get("content", ""),
        "model": f"ollama/{model}",
        "provider": "ollama",
        "latency_ms": latency_ms,
        "input_tokens": data.get("prompt_eval_count", 0),
        "output_tokens": data.get("eval_count", 0),
        "finish_reason": "stop",
    }


async def route_llm_request(
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.3,
    preferred_provider: Optional[str] = None,
) -> dict[str, Any]:
    """
    Route an LLM request through the provider fallback chain.

    Priority:
    1. Preferred provider (if specified and available)
    2. Groq (fast, free-tier)
    3. OpenAI (reliable, paid)
    4. Ollama (local fallback)

    Args:
        messages: Chat messages
        max_tokens: Max response tokens
        temperature: Sampling temperature
        preferred_provider: Override default routing

    Returns:
        Response dict from whichever provider succeeds
    """
    providers = _build_provider_chain(preferred_provider)

    last_error = None
    for provider_name, provider_fn in providers:
        try:
            logger.info("Attempting LLM call via %s", provider_name)
            result = await provider_fn(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            logger.info(
                "LLM response from %s in %dms (%d tokens)",
                provider_name,
                result.get("latency_ms", 0),
                result.get("output_tokens", 0),
            )
            return result

        except Exception as e:
            last_error = e
            logger.warning(
                "LLM provider %s failed: %s. Trying next...",
                provider_name, str(e)
            )
            continue

    # All providers failed
    logger.error("All LLM providers failed. Last error: %s", str(last_error))
    return {
        "answer": (
            "I apologize, but I'm unable to generate a response at this time. "
            "All AI providers are currently unavailable. Please try again shortly."
        ),
        "model": "fallback/error",
        "provider": "none",
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "finish_reason": "error",
        "error": str(last_error),
    }


def _build_provider_chain(
    preferred: Optional[str] = None,
) -> list[tuple[str, Any]]:
    """Build the ordered provider chain based on availability."""
    chain = []

    if preferred == "ollama":
        chain.append(("ollama", call_ollama))
    elif preferred == "openai" and settings.openai_api_key:
        chain.append(("openai", call_openai))
    elif preferred == "groq" and settings.groq_api_key:
        chain.append(("groq", call_groq))

    # Default chain
    if settings.groq_api_key and ("groq", call_groq) not in chain:
        chain.append(("groq", call_groq))
    if settings.openai_api_key and ("openai", call_openai) not in chain:
        chain.append(("openai", call_openai))
    if ("ollama", call_ollama) not in chain:
        chain.append(("ollama", call_ollama))

    return chain


def build_chat_messages(
    user_query: str,
    context: str = "",
    chat_history: Optional[list[dict[str, str]]] = None,
) -> list[dict[str, str]]:
    """
    Build the messages array for LLM call.

    Args:
        user_query: User's question
        context: RAG context from search
        chat_history: Previous messages in the session

    Returns:
        Messages in OpenAI chat format
    """
    if context:
        system = SYSTEM_PROMPT.format(context=context)
    else:
        system = NO_CONTEXT_PROMPT

    messages = [{"role": "system", "content": system}]

    # Add chat history (last 6 messages for context window management)
    if chat_history:
        messages.extend(chat_history[-6:])

    messages.append({"role": "user", "content": user_query})

    return messages
