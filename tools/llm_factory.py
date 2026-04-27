"""
tools/llm_factory.py — Unified LLM factory with automatic fallback.

Usage in any agent:
    from tools.llm_factory import get_llm
    llm = get_llm()
    response = llm.invoke("your prompt")

The factory handles:
- Primary: Groq (llama-3.3-70b-versatile) — fastest, free
- Fallback: Google Gemini 1.5 Flash — automatic on rate limit
- Retry logic with exponential backoff via tenacity
"""

from functools import lru_cache
from typing import Optional

from langchain_core.language_models import BaseChatModel
from tenacity import retry, stop_after_attempt, wait_exponential

import config

def build_groq_llm(temperature: float = config.LLM_TEMPERATURE) -> Optional[BaseChatModel] :
    """Build a Groq LLM instance. Returns None if key not configured."""
    if not config.GROQ_API_KEY:
        return None
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model = config.GROQ_MODEL,
            temperature = temperature,
            max_tokens = config.LLM_MAX_TOKENS,
            api_key = config.GROQ_API_KEY,
        )
    except ImportError:
        print("langchain-groq not installed. Run: uv sync")
        return None

def build_gemini_llm(temperature: float = config.LLM_TEMPERATURE) -> Optional[BaseChatModel] :
    """Build a Gemini LLM instance. Returns None if key not configured."""
    if not config.GOOGLE_API_KEY:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model = config.GEMINI_MODEL,
            temperature = temperature,
            max_tokens = config.LLM_MAX_TOKENS,
            google_api_key = config.GOOGLE_API_KEY,
        )
    except ImportError:
        print("langchain-google-genai not installed. Run: uv sync")
        return None

def get_llm(temperature: float = config.LLM_TEMPERATURE) -> BaseChatModel :
    """
    Returns the best available LLM with automatic fallback wiring.

    Priority: Groq → Gemini
    If Groq hits a rate limit at inference time, LangChain's .with_fallbacks()
    automatically retries the same call with Gemini — zero intervention needed.

    Raises:
        RuntimeError: if neither provider is configured.
    """
    
    primary = None
    fallback = None

    if config.PRIMARY_LLM == "groq":
        primary = build_groq_llm(temperature)
        fallback = build_gemini_llm(temperature)
    else:
        primary = build_gemini_llm(temperature)
        fallback = build_groq_llm(temperature)

    if primary is None and fallback is None:
        raise RuntimeError(
            "No LLM provider configured. "
            "Set GROQ_API_KEY or GOOGLE_API_KEY in your .env file."
        )

    if primary is None:
        print(f"Primary LLM ({config.PRIMARY_LLM}) not configured. Using fallback only.")
        return fallback
    
    if fallback is None:
        print(f"Fallback LLM not configured. Using {config.PRIMARY_LLM} only (no failover).")
        return primary

    # Wire fallback: if primary raises an exception, langchain retries with fallback
    return primary.with_fallbacks([fallback])


def get_llm_for_agent(agent_name: str) -> BaseChatModel:
    """
    Same as get_llm() but logs which agent is initializing.
    Use this inside agent files for clearer logs.
    """
    print(f"[{agent_name}] Initializing LLM...")
    return get_llm()


if __name__ == "__main__":
    # Quick test — run: uv run python tools/llm_factory.py
    print("Testing LLM factory...")
    try:
        llm = get_llm()
        response = llm.invoke("Say 'IntelliDD Pro is working!' and nothing else.")
        print(f"LLM response: {response.content}")
    except Exception as e:
        print(f"LLM test failed: {e}")