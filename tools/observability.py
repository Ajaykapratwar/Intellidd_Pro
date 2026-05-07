"""
tools/observability.py — LangSmith observability helpers.

Responsibilities:
  - Capture LangSmith trace URL after a pipeline run
  - Build per-agent performance summary (timing, tokens, cost)
  - Estimate token counts and cost for Groq/Gemini free tiers
  - Provide a safe no-op when LangSmith is not configured

Usage:
    from tools.observability import (
        get_langsmith_trace_url,
        build_performance_summary,
        estimate_tokens,
    )
"""

import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass, field

import config

# ── Token & cost estimation ───────────────────────────────────────────────────
# Approximate token counts per model (input + output per agent call)
# These are rough estimates — LangSmith shows exact counts in its dashboard

MODEL_COST_PER_1K_TOKENS = {
    # Groq free tier — $0 but useful to track relative usage
    "llama-3.3-70b-versatile": 0.0,
    "llama3-70b-8192":         0.0,
    # Gemini free tier — $0
    "gemini-1.5-flash":        0.0,
    "gemini-1.5-pro":          0.0,
}

# Rough average tokens per agent type (input prompt + output JSON)
AGENT_TOKEN_ESTIMATES = {
    "SeedCrawler":     4_000,
    "TeamAgent":       6_000,
    "InvestorAgent":   5_500,
    "PressAgent":      5_000,
    "FinancialsAgent": 5_500,
    "TechStackAgent":  6_000,
    "SocialAgent":     4_500,
    "CompetitorAgent": 7_000,
    "Validator":       8_000,
    "RiskScorer":      7_500,
    "DocumentRAG":     1_000,
    "Synthesis":       10_000,
}

def estimate_token(agent_name: str) -> int:
    """Estimate token usage for an agent by name."""
    return AGENT_TOKEN_ESTIMATES.get(agent_name, 5000)

def estimate_total_tokens(agent_timings: dict) -> int:
    """Estimate total tokens across all agents that ran."""
    total = 0
    for agent_name in agent_timings:
        agent_map = {
            "team": "TeamAgent",
            "investors": "InvestorsAgent",
            "press": "PressAgent",
            "financials": "FinancialsAgent",
            "tech_stack": "TechStackAgent",
            "social": "SocialAgent",
            "competitors": "CompetitorAgent",
            "seed": "SeedCrawler",
            "validation": "Validator",
            "risk": "RiskScorer",
            "rag": "DocumentRAG",
            "synthesis": "Synthesis",
        }
        mapped = agent_map.get(agent_name, agent_name)
        total += estimate_token(mapped)
    return total

# ── LangSmith trace URL capture ───────────────────────────────────────────────
def get_langsmith_trace_url(ls_run_id: str, max_wait_seconds: int = 8) -> Optional[str]:
    """
    Fetch the LangSmith trace URL for a specific run ID.

    LangSmith may take a few seconds to index the run after it completes.
    This function retries with a short wait before giving up.

    Args:
        ls_run_id:         The UUID passed as run_id to the LangGraph config
        max_wait_seconds:  Max seconds to wait for LangSmith to index the run

    Returns:
        Full URL string like:
            https://smith.langchain.com/o/.../projects/p/.../r/...
        or None if LangSmith is not configured / run not found.
    """

    if not config.LANGCHAIN_TRACING_V2:
        return None
    
    langsmith_api_key = config.LANGCHAIN_API_KEY if hasattr(config, 'LANGCHAIN_API_KEY') else ""
    if not langsmith_api_key:
        return None
    
    try:
        from langsmith import Client
        client = Client()

        deadline = time.time() + max_wait_seconds
        while time.time() < deadline:
            try:
                run = client.read_run(ls_run_id)
                if run:
                    trace_url = client.get_run_url(run=run)
                    print(f"  🔭 [Observability] LangSmith trace URL captured")
                    return trace_url
            except Exception:
                pass  # Ignore and retry
            time.sleep(3)
        print(f"  ⚠️  [Observability] LangSmith run not found after {max_wait_seconds}s")
        return None
    except ImportError:
        print(f"  ⚠️  [Observability] langcmith package not installed")
        return None
    except Exception as e:
        print(f"  ⚠️  [Observability] Could not fetch trace URL: {e}")
        return None

# ── Performance summary builder ───────────────────────────────────────────────
def build_performance_summary(
    agent_timings: dict, total_duration: float,
    trace_url: Optional[str], model_used: str, docs_uploaded: int = 0
) -> dict:
    """
    Build a structured performance summary from agent timing data.

    Args:
        agent_timings:   Dict of {agent_name: elapsed_seconds}
                         e.g. {"team": 14.3, "investors": 33.5, ...}
        total_duration:  Total pipeline wall-clock time in seconds
        trace_url:       LangSmith trace URL (or None)
        model_used:      LLM model name string
        docs_uploaded:   Number of documents processed via RAG

    Returns:
        Dict with full performance breakdown for display in UI.
    """
    if not agent_timings:
        return {}
    
    # find slowest and fastest agents
    sorted_timings = sorted(agent_timings.items(), key=lambda x: x[1], reverse=True)
    slowest_agent = sorted_timings[0][0] if sorted_timings else "unknown"
    fastest_agent = sorted_timings[-1][0] if sorted_timings else "unknown"

    # Estimate tokens
    total_tokens = estimate_total_tokens(agent_timings)

    # Parallel efficiency: if all specialists ran in parallel,
    # parallel time = max of their timings (not sum)
    specialist_keys = ["team", "investors", "press", "financials", "tech_stack", "social", "competitors"]

    specialist_timings = [agent_timings.get(k, 0) for k in specialist_keys if k in agent_timings]

    parallel_max = max(specialist_timings) if specialist_timings else 0
    parallel_sum = sum(specialist_timings)
    time_saved = round(parallel_sum - parallel_max, 1)
    efficiency_pct = round((time_saved / parallel_sum * 100) if parallel_sum > 0 else 0)

    # Build the summary
    return {
        "agent_timings": agent_timings,
        "total_duration": round(total_duration, 1),
        "slowest_agent": slowest_agent,
        "fastest_agent": fastest_agent,
        "total_tokens_est": total_tokens,
        "model_used": model_used,
        "trace_url": trace_url,
        "docs_uploaded": docs_uploaded,
        "parallel_time_saved_seconds": time_saved,
        "parallel_efficiency_pct": efficiency_pct,
        "langsmith_enabled": config.LANGCHAIN_TRACING_V2,
        "agent_count": len(agent_timings),
    }

def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{int(seconds)}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"

# ── LangSmith config checker ──────────────────────────────────────────────────

def check_langsmith_config() -> dict:
    """
    Check if LangSmith is properly configured.

    Returns:
        Dict with keys: enabled, has_key, project, status_message
    """
    langsmith_key = getattr(config, 'LANGCHAIN_API_KEY', '') or ""

    if not config.LANGCHAIN_TRACING_V2:
        return {
            "enabled": False,
            "has_key": bool(langsmith_key),
            "project": config.LANGCHAIN_PROJECT,
            "status_message": "LangSmith tracing disabled in config.py",
        }
    
    if not langsmith_key:
        return {
            "enabled": False,
            "has_key": False,
            "project": config.LANGCHAIN_PROJECT,
            "status_message": "LangSmith API key not set in config.py",
        }
    
    return {
        "enabled": True,
        "has_key": True,
        "project": config.LANGCHAIN_PROJECT,
        "status_message": "✅ LangSmith tracing enabled",
    }

if __name__ == "__main__":
    # Quick config check
    print("LangSmith config check:")
    result = check_langsmith_config()
    for k, v in result.items():
        print(f"  {k}: {v}")