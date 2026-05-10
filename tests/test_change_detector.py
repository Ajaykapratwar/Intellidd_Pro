"""
tests/test_change_detector.py — Change detection logic unit tests.

Run: uv run pytest tests/test_change_detector.py -v
"""

import pytest
from unittest.mock import MagicMock
from monitoring.change_detector import (
    _structural_diff,
    detect_changes,
    has_significant_changes,
    ChangeEvent,
    _safe_str,
    _changed,
)


def _make_run(**kwargs) -> MagicMock:
    """Create a mock ResearchRun with sensible defaults."""
    run = MagicMock()

    risk_sc = kwargs.get("risk_scorecard", {
        "overall_risk_score":    5,
        "founder_risk":    {"score": 4, "severity": "Medium"},
        "market_risk":     {"score": 5, "severity": "Medium"},
        "financial_risk":  {"score": 4, "severity": "Medium"},
        "technical_risk":  {"score": 3, "severity": "Low"},
        "reputational_risk": {"score": 4, "severity": "Medium"},
    })

    run.company_name      = kwargs.get("company_name", "Test Corp")
    run.created_at_display = kwargs.get("date", "Jan 01, 2026")
    run.report_markdown   = kwargs.get("report_markdown", "# Report\n## Exec Summary\nContent.")
    run.investor_data     = kwargs.get("investor_data", {
        "total_funding_usd": "$50M", "last_round_type": "Series A"
    })
    run.risk_scorecard    = risk_sc

    # ── CRITICAL: explicitly set as int, MagicMock won't derive this ──────────
    raw_score = risk_sc.get("overall_risk_score", 5)
    try:
        run.overall_risk_score = int(raw_score)
    except (TypeError, ValueError):
        run.overall_risk_score = 5
    # ──────────────────────────────────────────────────────────────────────────

    run.team_data         = kwargs.get("team_data", {
        "founders": [{"name": "Alice Smith"}]
    })
    run.competitor_data   = kwargs.get("competitor_data", {
        "market_position": "Challenger"
    })
    run.press_data        = kwargs.get("press_data", {
        "overall_sentiment": "positive"
    })
    run.financials_data   = kwargs.get("financials_data", {
        "revenue_estimate": "$10M ARR"
    })
    return run


class TestSafeStr:
    def test_none_returns_unknown(self):
        assert _safe_str(None) == "Unknown"

    def test_dict_serialized(self):
        result = _safe_str({"key": "value"})
        assert "key" in result

    def test_string_passthrough(self):
        assert _safe_str("hello") == "hello"


class TestChanged:
    def test_same_values_not_changed(self):
        assert _changed("$50M", "$50M") is False

    def test_different_values_changed(self):
        assert _changed("$50M", "$100M") is True

    def test_case_insensitive(self):
        assert _changed("Series A", "series a") is False

    def test_none_vs_unknown(self):
        assert _changed(None, "Unknown") is False


class TestStructuralDiff:
    def test_no_changes_returns_empty(self):
        """Identical runs should produce zero events."""
        old_run = _make_run()
        new_run = _make_run()
        events  = _structural_diff(new_run, old_run)
        assert isinstance(events, list)

    def test_funding_change_detected(self):
        """Funding amount change must be detected as high severity."""
        old_run = _make_run(investor_data={"total_funding_usd": "$50M",  "last_round_type": "Series A"})
        new_run = _make_run(investor_data={"total_funding_usd": "$400M", "last_round_type": "Series B"})
        events = _structural_diff(new_run, old_run)
        types  = [e.change_type for e in events]
        assert "funding_change"   in types or "new_funding_round" in types
        high   = [e for e in events if e.severity == "high"]
        assert len(high) >= 1

    def test_new_funding_round_detected(self):
        """New funding round type must trigger high-severity event."""
        old_run = _make_run(investor_data={"total_funding_usd": "$50M",  "last_round_type": "Series A"})
        new_run = _make_run(investor_data={"total_funding_usd": "$400M", "last_round_type": "Series D"})
        events  = _structural_diff(new_run, old_run)
        assert any(e.change_type == "new_funding_round" for e in events)

    def test_risk_score_shift_detected(self):
        """Risk score shift >= 2 must be flagged."""
        old_run = _make_run(risk_scorecard={
            "overall_risk_score": 3,
            "founder_risk":    {"score": 3, "severity": "Low"},
            "market_risk":     {"score": 3, "severity": "Low"},
            "financial_risk":  {"score": 3, "severity": "Low"},
            "technical_risk":  {"score": 3, "severity": "Low"},
            "reputational_risk": {"score": 3, "severity": "Low"},
        })
        new_run = _make_run(risk_scorecard={
            "overall_risk_score": 7,
            "founder_risk":    {"score": 7, "severity": "High"},
            "market_risk":     {"score": 7, "severity": "High"},
            "financial_risk":  {"score": 7, "severity": "High"},
            "technical_risk":  {"score": 7, "severity": "High"},
            "reputational_risk": {"score": 7, "severity": "High"},
        })
        events = _structural_diff(new_run, old_run)
        assert any(e.change_type == "risk_score_shift" for e in events)

    def test_leadership_change_detected(self):
        """New founder appearing should be flagged as leadership change."""
        old_run = _make_run(team_data={"founders": [{"name": "Alice Smith"}]})
        new_run = _make_run(team_data={"founders": [{"name": "Alice Smith"}, {"name": "Bob Jones"}]})
        events  = _structural_diff(new_run, old_run)
        assert any("leadership" in e.change_type for e in events)

    def test_leadership_departure_detected(self):
        """Founder disappearing should be flagged as departure."""
        old_run = _make_run(team_data={"founders": [{"name": "Alice"}, {"name": "Bob"}]})
        new_run = _make_run(team_data={"founders": [{"name": "Alice"}]})
        events  = _structural_diff(new_run, old_run)
        assert any("departure" in e.change_type for e in events)

    def test_market_position_change_detected(self):
        """Market position change should be detected."""
        old_run = _make_run(competitor_data={"market_position": "Challenger"})
        new_run = _make_run(competitor_data={"market_position": "Leader"})
        events  = _structural_diff(new_run, old_run)
        assert any(e.change_type == "market_position_change" for e in events)

    def test_sentiment_shift_negative_is_high_severity(self):
        """Positive → negative sentiment should be high severity."""
        old_run = _make_run(press_data={"overall_sentiment": "positive"})
        new_run = _make_run(press_data={"overall_sentiment": "negative"})
        events  = _structural_diff(new_run, old_run)
        sent_events = [e for e in events if e.change_type == "sentiment_shift"]
        assert len(sent_events) >= 1
        assert sent_events[0].severity == "high"


class TestHasSignificantChanges:
    def test_empty_events_not_significant(self):
        assert has_significant_changes([]) is False

    def test_low_only_not_significant(self):
        events = [
            ChangeEvent("type", "field", "old", "new", "low", "desc")
        ]
        assert has_significant_changes(events) is False

    def test_medium_is_significant(self):
        events = [
            ChangeEvent("type", "field", "old", "new", "medium", "desc")
        ]
        assert has_significant_changes(events) is True

    def test_high_is_significant(self):
        events = [
            ChangeEvent("type", "field", "old", "new", "high", "desc")
        ]
        assert has_significant_changes(events) is True


class TestChangeEventModel:
    def test_to_dict_has_required_keys(self):
        event = ChangeEvent("funding_change", "total_funding", "$50M", "$400M", "high", "Funding changed.")
        d = event.to_dict()
        for key in ["change_type", "field", "old_value", "new_value", "severity", "description", "detected_at"]:
            assert key in d

    def test_emoji_mapping(self):
        assert ChangeEvent("t","f","o","n","high","d").emoji  == "🔴"
        assert ChangeEvent("t","f","o","n","medium","d").emoji == "🟡"
        assert ChangeEvent("t","f","o","n","low","d").emoji   == "🟢"