"""
tools/llm_factory.py — Unified LLM factory with automatic fallback + retry.
"""

import time
import random
from functools import lru_cache
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

import config

logger = logging.getLogger(__name__)


def _build_groq_llm(temperature: float = config.LLM_TEMPERATURE) -> Optional[BaseChatModel]:
    """Build a Groq LLM instance. Returns None if key not configured."""
    if not config.GROQ_API_KEY:
        return None
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=config.GROQ_MODEL,
            temperature=temperature,
            max_tokens=config.LLM_MAX_TOKENS,
            api_key=config.GROQ_API_KEY,
        )
    except ImportError:
        print("langchain-groq not installed. Run: uv sync")
        return None


def _build_gemini_llm(temperature: float = config.LLM_TEMPERATURE) -> Optional[BaseChatModel]:
    """Build a Gemini LLM instance. Returns None if key not configured."""
    if not config.GOOGLE_API_KEY:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            temperature=temperature,
            max_output_tokens=config.LLM_MAX_TOKENS,
            google_api_key=config.GOOGLE_API_KEY,
        )
    except ImportError:
        print("langchain-google-genai not installed. Run: uv sync")
        return None


def get_llm(temperature: float = config.LLM_TEMPERATURE) -> BaseChatModel:
    """
    Returns the best available LLM with automatic fallback wiring.
    Priority: Groq → Gemini
    """
    primary = None
    fallback = None

    if config.PRIMARY_LLM == "groq":
        primary = _build_groq_llm(temperature)
        fallback = _build_gemini_llm(temperature)
    else:
        primary = _build_gemini_llm(temperature)
        fallback = _build_groq_llm(temperature)

    if primary is None and fallback is None:
        raise RuntimeError(
            "No LLM provider configured. "
            "Set GROQ_API_KEY or GOOGLE_API_KEY in your .env file."
        )

    if primary is None:
        print(f"Primary LLM ({config.PRIMARY_LLM}) not configured. Using fallback only.")
        return fallback

    if fallback is None:
        print(f"Fallback LLM not configured. Using {config.PRIMARY_LLM} only.")
        return primary

    return primary.with_fallbacks([fallback])


def get_llm_for_agent(agent_name: str) -> BaseChatModel:
    """Same as get_llm() but logs which agent is initializing."""
    print(f"[{agent_name}] Initializing LLM...")
    return get_llm()


def _is_rate_limit_error(exception: Exception) -> bool:
    """Check if an exception is a rate limit (429) error from any provider."""
    error_str = str(exception).lower()
    return (
        "rate_limit_exceeded" in error_str
        or "rate limit" in error_str
        or "429" in error_str
        or "tokens per minute" in error_str
        or "tokens per day" in error_str
        or "too many requests" in error_str
    )


def call_llm_with_retry(
    llm: BaseChatModel,
    messages: list,
    agent_name: str = "Agent",
    max_attempts: int = 5,
) -> BaseMessage:
    """
    Call an LLM with automatic retry on rate limit errors.

    Strategy:
    - On 429 rate limit: wait with exponential backoff (5s → 10s → 20s → 40s)
    - Adds small random jitter so parallel agents don't all retry at same time
    - After max_attempts, raises the last exception

    Args:
        llm:          The LLM instance from get_llm_for_agent()
        messages:     List of LangChain message objects
        agent_name:   For logging only
        max_attempts: Max retry attempts before giving up (default 5)

    Returns:
        LLM response message

    Usage in any agent (replace llm.invoke(...) with this):
        from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
        llm = get_llm_for_agent(AGENT_NAME)
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
    """
    attempt = 0
    wait_seconds = 5  # start with 5s wait

    while attempt < max_attempts:
        try:
            # Small stagger delay before every LLM call
            # Prevents all parallel agents from hitting API simultaneously
            stagger = random.uniform(0.5, 2.5)
            time.sleep(stagger)

            response = llm.invoke(messages)
            return response

        except Exception as e:
            attempt += 1

            if _is_rate_limit_error(e):
                if attempt >= max_attempts:
                    print(f"[{agent_name}] Rate limit hit {max_attempts} times. Giving up.")
                    raise

                # Parse wait time from error message if available
                # Groq errors say "Please try again in 1.93s" or "in 1h2m26s"
                suggested_wait = _parse_wait_time(str(e))

                if suggested_wait and suggested_wait < 120:
                    # Use Groq's suggested wait + small buffer
                    actual_wait = suggested_wait + random.uniform(1, 3)
                    print(
                        f"[{agent_name}] Rate limit hit. "
                        f"Groq says wait {suggested_wait:.1f}s. "
                        f"Waiting {actual_wait:.1f}s then retrying "
                        f"(attempt {attempt}/{max_attempts})..."
                    )
                else:
                    # Use exponential backoff: 5 → 10 → 20 → 40s
                    actual_wait = wait_seconds + random.uniform(0, 3)
                    print(
                        f"[{agent_name}] Rate limit hit. "
                        f"Waiting {actual_wait:.1f}s then retrying "
                        f"(attempt {attempt}/{max_attempts})..."
                    )
                    wait_seconds = min(wait_seconds * 2, 60)  # cap at 60s

                time.sleep(actual_wait)

            else:
                # Non-rate-limit error — don't retry, raise immediately
                raise

    raise RuntimeError(f"[{agent_name}] Failed after {max_attempts} attempts")


def _parse_wait_time(error_message: str) -> Optional[float]:
    """
    Parse the suggested wait time from a Groq rate limit error message.

    Groq errors contain strings like:
      "Please try again in 1.93s"
      "Please try again in 1h2m26.304s"
      "Please try again in 4m4.512s"

    Returns total seconds as float, or None if unparseable.
    """
    import re

    # Try simple seconds: "in 1.93s"
    match = re.search(r'try again in ([\d.]+)s', error_message)
    if match:
        return float(match.group(1))

    # Try minutes+seconds: "in 4m4.512s"
    match = re.search(r'try again in (\d+)m([\d.]+)s', error_message)
    if match:
        return int(match.group(1)) * 60 + float(match.group(2))

    # Try hours+minutes+seconds: "in 1h2m26.304s"
    match = re.search(r'try again in (\d+)h(\d+)m([\d.]+)s', error_message)
    if match:
        hours = int(match.group(1))
        mins = int(match.group(2))
        secs = float(match.group(3))
        total = hours * 3600 + mins * 60 + secs
        # If it's asking to wait hours, cap at 60s and use backoff instead
        return min(total, 60.0)

    return None


if __name__ == "__main__":
    print("Testing LLM factory...")
    try:
        llm = get_llm()
        from langchain_core.messages import HumanMessage
        response = call_llm_with_retry(
            llm,
            [HumanMessage(content="Say 'IntelliDD Pro is working!' and nothing else.")],
            agent_name="Test"
        )
        print(f"LLM response: {response.content}")
    except Exception as e:
        print(f"LLM test failed: {e}")