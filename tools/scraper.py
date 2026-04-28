"""
tools/scraper.py — Unified web scraper with 3-layer graceful degradation.

Layer 1: Firecrawl (clean markdown output, handles JS)  — if API key set
Layer 2: Playwright (headless browser)                  — always available
Layer 3: requests + BeautifulSoup                       — fastest fallback

Usage in any agent:
    from tools.scraper import scrape_url
    result = scrape_url("https://example.com")
    print(result.text)      # cleaned text content
    print(result.success)   # True/False
    print(result.source)    # which scraper was used
"""

import time
import re
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

import config

@dataclass
class ScrapeResult:
    """Structured results from any scraper layer."""
    url: str
    text: str
    title: str = ""
    success: bool = True
    source: str = ""
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __bool__(self):
        return self.success and bool(self.text.strip())

def _clean_text(text: str) -> str:
    """Removes excessive whitespace and normalize the line breaks."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    return text

# Layer 1 : Firecrawl
def _scrape_firecrawl(url: str) -> ScrapeResult:
    """
    Scrape using Firecrawl API — returns clean markdown.
    Only called if FIRECRAWL_API_KEY is set.
    """
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
        result = app.scrape(
            url,
            formats=["markdown"],
            only_main_content=True
        )
        if result and result.get("markdown"):
            return ScrapeResult(
                url = url,
                text = _clean_text(result["markdown"]),
                title=result.get("metadata", {}).get("title", ""),
                source="firecrawl",
                metadata=result.get("metadata", ""),
            )
        return ScrapeResult(url=url, text="", success=False, source="firecrawl", error="Empty response from firecrawl")
    
    except Exception as e:
        return ScrapeResult(url=url, text="", title="", success=False, source="firecrawl", error=str(e))

# Layer 2 : Playwright
def _scrape_playwright(url: str) -> ScrapeResult:
    """
    Scrape using Playwright headless browser.
    Good for JS-heavy pages (React, Next.js, etc.)
    Requires: playwright install chromium (run once after uv sync)
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=config.PLAYWRIGHT_HEADLESS)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )

            # Block images/fonts to speed up loading
            page.route("**/*.{png, jpg, jpeg, gif, webp, svg, woff, woff2, ttf}", lambda route: route.abort())

            page.goto(url, wait_until="networkidle", timeout=config.PLAYWRIGHT_TIMEOUT_MS)

            title = page.title()
            html = page.content()
            browser.close()

        # Parse with BS4
        soup = BeautifulSoup(html, "lxml")

        # Remove non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator="\n")

        return ScrapeResult(
            url=url,
            text=_clean_text(text),
            title=title,
            source="playwright"
        )
    
    except Exception as e:
        return ScrapeResult(url=url, text="", title="", success=False, source="playwright", error=str(e))

# Layer 3 : requests + BeautifulSoup
def _scrape_bs4(url: str) -> ScrapeResult:
    """
    Scrape using plain requests + BeautifulSoup.
    Fast and reliable for static pages. No JS rendering.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Remove non-content tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else ""
        text = soup.get_text(separator="\n")

        return ScrapeResult(
            url=url,
            text=_clean_text(text),
            title=title,
            source="bs4"
        )
    except Exception as e:
        return ScrapeResult(url=url, text="", title="", success=False, source="bs4", error=str(e))

# Public Interface
def scrape_url(url: str, prefer_js: bool = False) -> ScrapeResult:
    """
    Scrape a URL using the best available method.

    Args:
        url: The URL to scrape.
        prefer_js: If True, tries Playwright before Firecrawl.
                   Use for known JS-heavy pages.

    Returns:
        ScrapeResult with .text, .success, .source

    Degradation order (default):
        Firecrawl → Playwright → BS4

    Degradation order (prefer_js=True):
        Playwright → Firecrawl → BS4
    """
    time.sleep(config.SCRAPE_DELAY_SECONDS)  # Polite Delay

    scrapers = []

    if prefer_js:
        scrapers = [_scrape_playwright]
        if config.USE_FIRECRAWL:
            scrapers.append(_scrape_firecrawl)
    else :
        if config.USE_FIRECRAWL:
            scrapers = [_scrape_firecrawl, _scrape_playwright, _scrape_bs4]
        else :
            scrapers = [_scrape_playwright, _scrape_bs4]

    # Always ensure BS4 is the final fallback
    if _scrape_bs4 not in scrapers:
        scrapers.append(_scrape_bs4)
    
    for scrapper in scrapers:
        result = scrapper(url)
        if result: # __bool__ checks success + non-empty text
            print(f"Scraped [{result.source}]: {url[:60]}...")
            return result
        else:
            print(f"[{result.source}] failed for {url[:60]}: {result.error}")
    
    # All scrapers failed
    return ScrapeResult(
        url=url,
        text="",
        success=False,
        source="none",
        error="All scraping layers failed",
    )

if __name__ == "__main__":
    # Quick test — run: uv run python tools/scraper.py
    test_url = "https://stripe.com/"
    print(f"Testing scraper on: {test_url}\n")
    result = scrape_url(test_url)
    if result:
        print(f"Success via [{result.source}]")
        print(f"   Title: {result.title}")
        print(f"   Text length: {len(result.text)} chars")
        print(f"   Preview: {result.text[:300]}...")
    else:
        print(f"All scrapers failed: {result.error}")