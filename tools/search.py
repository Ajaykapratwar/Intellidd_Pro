"""
tools/search.py — DuckDuckGo web search wrapper.

No API key required. Works out of the box.

Usage in any agent:
    from tools.search import search_web
    results = search_web("Stripe funding rounds 2024")
    for r in results:
        print(r.title, r.url, r.snippet)
"""

import time
import random

from dataclasses import dataclass
from typing import Optional

from ddgs import DDGS

import config

@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str

    def to_text(self) -> str:
        """Format as a readable block for LLM context."""
        return f"Title: {self.title}\nURL: {self.url}\nSnippet: {self.snippet}\n---"

def search_web(query:str, max_results: int = config.SEARCH_MAX_RESULTS, region:str = config.SEARCH_REGION,) -> list[SearchResult]:
    """
    Search the web using DuckDuckGo.

    Args:
        query:       The search query string.
        max_results: Number of results to return (default from config).
        region:      Region code for results (default: worldwide).

    Returns:
        List of SearchResult objects. Empty list on failure.
    """

    # Small random delay to be polite and avoid blocks
    time.sleep(random.uniform(0.5, 1.5))

    try:
        results = []
        with DDGS() as ddgs:
            raw = ddgs.text(query, region=region, max_results=max_results)

            for r in raw:
                results.append(SearchResult(
                    title = r.get("title", ""),
                    url = r.get("href", ""),
                    snippet = r.get("body", "")
                ))
        print(f"Searched: '{query[:60]}' -> {len(results)} results")
        return results
    
    except Exception as e:
        print(f"Search failed for '{query[:50]}': {e}")
        return []
    
def search_to_context(query: str, max_results: int = 5) -> str:
    """
    Search and return results as a single formatted string for LLM prompts.

    Usage:
        context = search_to_context("Stripe investors 2024")
        # Pass context directly into your LLM prompt
    """

    results = search_web(query=query, max_results=max_results)
    if not results:
        return f"No search results found for {query}"

    blocks = [f"[Result {i+1}]\n{r.to_text()}" for i, r in enumerate(results)]
    return "\n\n".join(blocks)


if __name__ == "__main__":
    # Quick test — run: uv run python tools/search.py
    print("Testing DuckDuckGo search...\n")
    results = search_web("Stripe startup funding rounds site:crunchbase.com", max_results=5)
    if results:
        print(f"Got {len(results)} results:\n")
        for r in results:
            print(f"  • {r.title}")
            print(f"  🔗 {r.url}")
            print(f"  📝 {r.snippet[:100]}...")
            print()
    else:
        print("No results returned")