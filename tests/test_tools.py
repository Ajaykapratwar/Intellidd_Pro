"""
tests/test_tools.py — Tool wrapper unit tests.

Uses mocking to avoid real API calls.
Run: uv run pytest tests/test_tools.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSearchTool:
    """Tests for tools/search.py"""

    def test_search_result_dataclass(self):
        """SearchResult must have title, url, snippet, and to_text()."""
        from tools.search import SearchResult
        r = SearchResult(title="Test", url="https://example.com", snippet="A test snippet.")
        assert r.title   == "Test"
        assert r.url     == "https://example.com"
        assert r.snippet == "A test snippet."
        text = r.to_text()
        assert "Test" in text
        assert "https://example.com" in text

    def test_search_web_returns_list(self):
        """search_web() must return a list."""
        from tools.search import search_web
        mock_results = [
            {"title": "Test", "href": "https://example.com", "body": "snippet"},
        ]
        with patch("tools.search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = mock_results
            results = search_web("test query", max_results=1)
        assert isinstance(results, list)

    def test_search_web_returns_empty_on_error(self):
        """search_web() must return [] on any exception."""
        from tools.search import search_web
        with patch("tools.search.DDGS", side_effect=Exception("Connection error")):
            results = search_web("test query")
        assert results == []

    def test_search_to_context_returns_string(self):
        """search_to_context() must return a string."""
        from tools.search import search_to_context
        with patch("tools.search.search_web", return_value=[]):
            result = search_to_context("test query")
        assert isinstance(result, str)
        assert "No search results" in result

    def test_search_to_context_formats_results(self):
        """search_to_context() must format results into readable blocks."""
        from tools.search import search_to_context, SearchResult
        mock_results = [
            SearchResult("Title 1", "https://a.com", "Snippet 1"),
            SearchResult("Title 2", "https://b.com", "Snippet 2"),
        ]
        with patch("tools.search.search_web", return_value=mock_results):
            result = search_to_context("test")
        assert "Title 1" in result
        assert "https://a.com" in result
        assert "Result 1" in result


class TestScraperTool:
    """Tests for tools/scraper.py"""

    def test_scrape_result_dataclass(self):
        """ScrapeResult must have required fields and bool behavior."""
        from tools.scraper import ScrapeResult
        r = ScrapeResult(url="https://example.com", text="Content here", source="bs4")
        assert bool(r) is True

        empty = ScrapeResult(url="https://example.com", text="", success=False, source="bs4")
        assert bool(empty) is False

    def test_clean_text_normalizes_whitespace(self):
        """_clean_text must collapse multiple spaces and newlines."""
        from tools.scraper import _clean_text
        messy = "Hello    world\n\n\n\nGoodbye   "
        clean = _clean_text(messy)
        assert "    " not in clean
        assert "\n\n\n" not in clean
        assert clean.strip() == clean

    def test_bs4_scraper_returns_result(self):
        """_scrape_bs4 must return ScrapeResult even on error."""
        from tools.scraper import _scrape_bs4
        with patch("tools.scraper.requests.get", side_effect=Exception("timeout")):
            result = _scrape_bs4("https://example.com")
        assert result.success is False
        assert result.error is not None

    def test_scrape_url_falls_back_gracefully(self):
        """scrape_url must return a ScrapeResult even when all scrapers fail."""
        from tools.scraper import scrape_url
        with patch("tools.scraper.config.USE_FIRECRAWL", False), \
             patch("tools.scraper._scrape_playwright", return_value=MagicMock(
                 __bool__=lambda s: False, error="playwright error", source="playwright"
             )), \
             patch("tools.scraper._scrape_bs4", return_value=MagicMock(
                 __bool__=lambda s: False, error="bs4 error", source="bs4"
             )):
            result = scrape_url("https://example.com")
        assert result is not None


class TestLLMFactory:
    """Tests for tools/llm_factory.py"""

    def test_is_rate_limit_error_detection(self):
        """_is_rate_limit_error must detect all rate limit variants."""
        from tools.llm_factory import _is_rate_limit_error
        assert _is_rate_limit_error(Exception("rate_limit_exceeded")) is True
        assert _is_rate_limit_error(Exception("429 Too Many Requests")) is True
        assert _is_rate_limit_error(Exception("tokens per minute")) is True
        assert _is_rate_limit_error(Exception("tokens per day")) is True
        assert _is_rate_limit_error(Exception("rate limit reached")) is True
        assert _is_rate_limit_error(Exception("model not found")) is False
        assert _is_rate_limit_error(Exception("connection timeout")) is False

    def test_parse_wait_time_seconds(self):
        """_parse_wait_time must parse 'try again in Xs' format."""
        from tools.llm_factory import _parse_wait_time
        assert _parse_wait_time("Please try again in 1.93s. More info") == pytest.approx(1.93)
        assert _parse_wait_time("try again in 5.0s") == pytest.approx(5.0)

    def test_parse_wait_time_minutes_seconds(self):
        """_parse_wait_time must parse 'try again in XmYs' format."""
        from tools.llm_factory import _parse_wait_time
        result = _parse_wait_time("try again in 4m4.512s")
        assert result == pytest.approx(4 * 60 + 4.512)

    def test_parse_wait_time_hours_capped(self):
        """_parse_wait_time must cap very long waits at 60s."""
        from tools.llm_factory import _parse_wait_time
        result = _parse_wait_time("try again in 1h2m26.304s")
        assert result <= 60.0

    def test_parse_wait_time_invalid(self):
        """_parse_wait_time must return None for unparseable strings."""
        from tools.llm_factory import _parse_wait_time
        assert _parse_wait_time("no time info here") is None
        assert _parse_wait_time("") is None