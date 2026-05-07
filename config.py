"""
config.py — Central configuration for IntelliDD Pro.

Every constant, env var, and path lives here.
Other modules import from this file — never read os.environ directly.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before anything else
load_dotenv()


# Project Root
ROOT_DIR = Path(__file__).parent
OUTPUTS_DIR = ROOT_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)


# LLM Config
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# Model names — change here to switch models globally
GROQ_MODEL: str = "llama-3.3-70b-versatile"
GEMINI_MODEL: str = "gemini-1.5-flash"

# Which provider to try first
PRIMARY_LLM: str = "groq"      # "groq" | "gemini"
FALLBACK_LLM: str = "gemini"   # used when primary hits rate limit

# LLM generation settings
LLM_TEMPERATURE: float = 0.1   # Low temp for factual DD research
LLM_MAX_TOKENS: int = 4096


# Scraping Config
FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")

# Scraper preference order: firecrawl → playwright → requests+bs4
# If FIRECRAWL_API_KEY is empty, automatically skips to playwright
USE_FIRECRAWL: bool = bool(FIRECRAWL_API_KEY)

# Playwright settings
PLAYWRIGHT_TIMEOUT_MS: int = 30_000      # 30s page load timeout
PLAYWRIGHT_HEADLESS: bool = True

# Polite delay between scrape requests (seconds) — avoids IP blocks
SCRAPE_DELAY_SECONDS: float = 1.5


# Search Config
# DuckDuckGo — no API key needed
SEARCH_MAX_RESULTS: int = 8       # results per DuckDuckGo query
SEARCH_REGION: str = "wt-wt"      # worldwide results


# Agent Pipeline Config
MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "7"))
AGENT_TIMEOUT_SECONDS: int = int(os.getenv("AGENT_TIMEOUT_SECONDS", "90"))


# Persistence Config
DB_PATH: str = os.getenv("DB_PATH", str(ROOT_DIR / "intellidd.db"))
CHROMA_PATH: str = os.getenv("CHROMA_PATH", str(ROOT_DIR / "chroma_store"))


# Observability
LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "intellidd-pro")
LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "")

# Set these for LangSmith — LangGraph picks them up automatically
if LANGCHAIN_TRACING_V2:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = LANGCHAIN_PROJECT
    os.environ["LANGCHAIN_API_KEY"] = LANGCHAIN_API_KEY


# Alerting Config (Phase 7)
ALERT_EMAIL_FROM: str = os.getenv("ALERT_EMAIL_FROM", "")
ALERT_EMAIL_PASSWORD: str = os.getenv("ALERT_EMAIL_PASSWORD", "")
ALERT_SLACK_WEBHOOK: str = os.getenv("ALERT_SLACK_WEBHOOK", "")


# Validation
def validate_config() -> list[str]:
    """
    Returns a list of warning messages for missing/misconfigured values.
    Call this at startup to show the user what's not configured.
    """
    warnings = []

    if not GROQ_API_KEY and not GOOGLE_API_KEY:
        warnings.append(
            "CRITICAL: Neither GROQ_API_KEY nor GOOGLE_API_KEY is set. "
            "At least one LLM provider is required."
        )
    elif not GROQ_API_KEY:
        warnings.append(
            "GROQ_API_KEY not set. Will use Gemini as primary LLM. "
            "Get a free Groq key at console.groq.com"
        )
    elif not GOOGLE_API_KEY:
        warnings.append(
            "GOOGLE_API_KEY not set. No fallback LLM available. "
            "Get a free key at aistudio.google.com"
        )

    if not FIRECRAWL_API_KEY:
        warnings.append(
            "FIRECRAWL_API_KEY not set. "
            "Using Playwright + BeautifulSoup for scraping (still works, slightly slower)."
        )

    if not LANGCHAIN_TRACING_V2:
        warnings.append(
            "LangSmith tracing disabled. "
            "Set LANGCHAIN_TRACING_V2=true to enable agent observability."
        )

    return warnings


if __name__ == "__main__":
    # Quick config check — run: uv run python config.py
    issues = validate_config()
    if issues:
        for w in issues:
            print(w)
    else:
        print("All configuration looks good!")
    print(f"\nActive LLM:  {PRIMARY_LLM} ({GROQ_MODEL if PRIMARY_LLM == 'groq' else GEMINI_MODEL})")
    print(f"Firecrawl:   {'enabled' if USE_FIRECRAWL else 'disabled (using BS4 fallback)'}")
    print(f"LangSmith:   {'enabled' if LANGCHAIN_TRACING_V2 else 'disabled'}")
    print(f"DB path:     {DB_PATH}")