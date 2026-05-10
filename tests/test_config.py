"""
tests/test_config.py — Configuration and environment validation tests.

Run: uv run pytest tests/test_config.py -v
"""

import os
import pytest


class TestConfigLoading:
    """Test that config module loads and exposes expected attributes."""

    def test_config_imports(self):
        """Config module must import without error."""
        import config
        assert config is not None

    def test_required_attributes_exist(self):
        """All expected config attributes must exist."""
        import config
        required = [
            "GROQ_API_KEY", "GOOGLE_API_KEY", "FIRECRAWL_API_KEY",
            "GROQ_MODEL", "GEMINI_MODEL", "PRIMARY_LLM", "FALLBACK_LLM",
            "LLM_TEMPERATURE", "LLM_MAX_TOKENS",
            "USE_FIRECRAWL", "SCRAPE_DELAY_SECONDS",
            "SEARCH_MAX_RESULTS", "SEARCH_REGION",
            "MAX_WORKERS", "AGENT_TIMEOUT_SECONDS",
            "DB_PATH", "CHROMA_PATH",
            "LANGCHAIN_TRACING_V2", "LANGCHAIN_PROJECT",
            "OUTPUTS_DIR",
        ]
        for attr in required:
            assert hasattr(config, attr), f"config.{attr} is missing"

    def test_llm_temperature_range(self):
        """LLM temperature must be between 0 and 1."""
        import config
        assert 0.0 <= config.LLM_TEMPERATURE <= 1.0

    def test_max_workers_positive(self):
        """MAX_WORKERS must be a positive integer."""
        import config
        assert isinstance(config.MAX_WORKERS, int)
        assert config.MAX_WORKERS > 0

    def test_agent_timeout_positive(self):
        """AGENT_TIMEOUT_SECONDS must be positive."""
        import config
        assert config.AGENT_TIMEOUT_SECONDS > 0

    def test_outputs_dir_created(self):
        """OUTPUTS_DIR should be created on import."""
        import config
        assert config.OUTPUTS_DIR.exists()

    def test_primary_llm_valid(self):
        """PRIMARY_LLM must be 'groq' or 'gemini'."""
        import config
        assert config.PRIMARY_LLM in ("groq", "gemini")

    def test_search_max_results_positive(self):
        """SEARCH_MAX_RESULTS must be at least 1."""
        import config
        assert config.SEARCH_MAX_RESULTS >= 1


class TestValidateConfig:
    """Test the validate_config() function."""

    def test_validate_config_returns_list(self):
        """validate_config() must always return a list."""
        import config
        result = config.validate_config()
        assert isinstance(result, list)

    def test_validate_config_no_keys_gives_warnings(self):
        """Without API keys, validate_config should return at least one warning."""
        import config

        original_groq   = config.GROQ_API_KEY
        original_google = config.GOOGLE_API_KEY

        config.GROQ_API_KEY   = ""
        config.GOOGLE_API_KEY = ""

        warnings = config.validate_config()
        assert len(warnings) > 0
        assert any("CRITICAL" in w or "GROQ" in w for w in warnings)

        config.GROQ_API_KEY   = original_groq
        config.GOOGLE_API_KEY = original_google

    def test_model_names_are_strings(self):
        """Model names must be non-empty strings."""
        import config
        assert isinstance(config.GROQ_MODEL, str) and len(config.GROQ_MODEL) > 0
        assert isinstance(config.GEMINI_MODEL, str) and len(config.GEMINI_MODEL) > 0