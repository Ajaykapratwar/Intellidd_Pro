"""
monitoring/change_detector.py — Detect meaningful changes between two research runs.

Two-layer detection:
  Layer 1 — Structural diff: fast comparison of key JSON fields (no LLM).
             Catches: funding changes, risk score shifts, new founders, etc.

  Layer 2 — Semantic analysis: LLM reviews both reports and identifies
             nuanced changes the structural diff might miss.

Usage:
    from monitoring.change_detector import detect_changes
    events = detect_changes(new_run, old_run)
    for event in events:
        print(event.severity, event.description)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from persistence.models import ResearchRun

# ── Change event model ────────────────────────────────────────────────────────

@dataclass
class ChangeEvent():
    """Represents a single detected change between two runs."""
    change_type: str
    field: str
    old_value: str
    new_value: str
    severity: str
    description: str
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            'change_type': self.change_type,
            'field': self.field,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'severity': self.severity,
            'description': self.description,
            'detected_at': self.detected_at
        }
    
    @property
    def emoji(self) -> str:
        return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(self.severity, "⚪")
    
# ── Helper ────────────────────────────────────────────────────────────────────

def _safe_str(val) -> str:
    """convert any value to a clean comparable string."""
    if val is None:
        return "Unknown"
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)[:200]
    return str(val).strip()

def _changed(a, b) -> bool:
    """Returns True if two values are meaningfully different."""
    return _safe_str(a).lower() != _safe_str(b).lower()

def _try_float(val) -> Optional[float]:
    """Try to parse a numeric value from a string like '$400M' or '7'."""
    import re
    if val is None:
        return None
    s = str(val)

    cleaned = re.sub(r'[^\d.]', '', s.replace(",", ""))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

# ── Layer 1: Structural diff ──────────────────────────────────────────────────

def _structural_diff(new_run: ResearchRun, old_run: ResearchRun) -> list[ChangeEvent]:
    """
    Fast field-by-field comparison of key metrics.
    No LLM needed — just compares JSON values directly.
    """
    events = []

    # ── Funding changes ───────────────────────────────────────────────────────
    old_funding = old_run.investor_data.get("total_funding_usd", "Unknown")
    new_funding = new_run.investor_data.get("total_funding_usd", "Unknown")

    if _changed(old_funding, new_funding):
        events.append(ChangeEvent(
            change_type="funding _change",
            field="total_funding_usd",
            old_value=_safe_str(old_funding),
            new_value=_safe_str(new_funding),
            severity="high",
            description=(f"Total funding changed from {_safe_str(old_funding)} to {_safe_str(new_funding)}."
                f"This may indicate a new funding round.")
        ))

    old_round = old_run.investor_data.get("last_round_type", "Unknown")
    new_round = new_run.investor_data.get("last_round_type", "Unknown")

    if _changed(old_round, new_round) and new_round != "Unknown":
        events.append(ChangeEvent(
            change_type="new_funding_round",
            field="last_round_type",
            old_value=_safe_str(old_round),
            new_value=_safe_str(new_round),
            severity="high",
            description=(f"Last funding round changed from {_safe_str(old_round)} to {_safe_str(new_round)}."
                f"This may indicate a new funding event.")
        ))
    
    # ── Risk score changes ────────────────────────────────────────────────────
    try:
        old_risk = int(old_run.overall_risk_score)
        new_risk = int(new_run.overall_risk_score)
    except (TypeError, ValueError):
        old_risk = None
        new_risk = None

    if old_risk is not None and new_risk is not None:
        delta = abs(new_risk - old_risk)
        if delta >= 2:
            direction = "increased" if new_risk > old_risk else "decreased"
            severity = "high" if delta >= 3 else "medium"
            events.append(ChangeEvent(
                change_type="risk_score_shift",
                field="overall_risk_score",
                old_value=f"{old_risk}/10",
                new_value=f"{new_risk}/10",
                severity=severity,
                description=(
                    f"Overall risk score {direction} by {delta} points "
                    f"({old_risk}/10 → {new_risk}/10)."
                ),
            ))
    
    # ── Individual risk dimensions ────────────────────────────────────────────
    risk_dims = [
        "founder_risk", "market_risk", "financial_risk",
        "technical_risk", "reputational_risk"
    ]

    for dim in risk_dims:
        old_score = old_run.risk_scorecard.get(dim, {}).get("score")
        new_score = new_run.risk_scorecard.get(dim, {}).get("score")

        try:
            o, n = int(old_score), int(new_score)
            if abs(n - o) >= 3:
                direction = "worseend" if n > o else "improved"
                events.append(ChangeEvent(
                    change_type="risk_dimension_shift",
                    field=dim,
                    old_value=f"{o}/10",
                    new_value=f"{n}/10",
                    severity="medium",
                    description=(
                        f"{dim.replace('_', ' ').title()} has {direction} "
                        f"Significantly ({o}/10 → {n}/10)."
                    ),
                ))
        except (TypeError, ValueError):
            pass
    
    # ── Leadership changes ────────────────────────────────────────────────────
    old_founders = {
        f.get("name", "").lower()
        for f in old_run.team_data.get("founders", [])
        if f.get("name")
    }
    new_founders = {
        f.get("name", "").lower()
        for f in new_run.team_data.get("founders", [])
        if f.get("name")
    }

    added = new_founders - old_founders
    removed = old_founders - new_founders

    if added:
        events.append(ChangeEvent(
            change_type="leadership_change",
            field="founders",
            old_value=", ".join(old_founders) or None,
            new_value=", ".join(new_founders) or None,
            severity="medium",
            description=f"New founder(s) added: {', '.join(added)}."
        ))
    
    if removed:
        events.append(ChangeEvent(
            change_type="leadership_departure",
            field="founders",
            old_value=", ".join(old_founders) or None,
            new_value=", ".join(new_founders) or None,
            severity="high",
            description=f"Founder(s) removed: {', '.join(removed)}."
        ))
    
    # ── Market position change ────────────────────────────────────────────────
    old_pos = old_run.competitor_data.get("market_position", "Unknown")
    new_pos = new_run.competitor_data.get("market_position", "Unknown")

    if _changed(old_pos, new_pos) and "Unknown" not in (old_pos, new_pos):
        events.append(ChangeEvent(
            change_type="market_position_change",
            field="market_position",
            old_value=_safe_str(old_pos),
            new_value=_safe_str(new_pos),
            severity="medium",
            description=(
                f"Market position shifted from {_safe_str(old_pos)} to {_safe_str(new_pos)}."
            ),
        ))
    
    # ── Press sentiment shift ─────────────────────────────────────────────────
    old_sentiment = old_run.press_data.get("overall_sentiment", "Unknown")
    new_sentiment = new_run.press_data.get("overall_sentiment", "Unknown")

    if _changed(old_sentiment, new_sentiment) and "Unknown" not in (old_sentiment, new_sentiment):
        # Negative to positive = low, Positive to negative = high
        severity = "high" if new_sentiment == "negative" else "low"
        events.append(ChangeEvent(
            change_type="sentiment_shift",
            field="overall_sentiment",
            old_value=_safe_str(old_sentiment),
            new_value=_safe_str(new_sentiment),
            severity=severity,
            description=(
                f"Press sentiment changed from '{old_sentiment}' to '{new_sentiment}'."
            ),
        ))

    # ── Revenue estimate change ───────────────────────────────────────────────
    old_rev = old_run.financials_data.get("revenue_estimate", "Unknown")
    new_rev = new_run.financials_data.get("revenue_estimate", "Unknown")

    if _changed(old_rev, new_rev) and "Unknown" not in (old_rev, new_rev):
        events.append(ChangeEvent(
            change_type="revenue_change",
            field="revenue_estimate",
            old_value=_safe_str(old_rev),
            new_value=_safe_str(new_rev),
            severity="medium",
            description=f"Revenue estimate changed: {old_rev} → {new_rev}.",
        ))

    return events

# ── Layer 2: LLM semantic analysis ───────────────────────────────────────────

def _llm_semantic_diff(new_run: ResearchRun, old_run: ResearchRun, structural_event: list[ChangeEvent]) -> list[ChangeEvent]:
    """
    Use LLM to find semantic changes the structural diff missed.
    Compares the two report markdowns and identifies narrative shifts.
    Only runs if both reports have content — skips gracefully if LLM fails.
    """
    if not new_run.report_markdown or not old_run.report_markdown:
        return []

    # Only send the executive summaries + risk sections to save tokens
    def _extract_sections(md: str, max_chars: int = 2000) -> str:
        lines = md.split("\n")
        relevant = []
        capture = False
        for line in lines:
            if any(h in line for h in["## Executive", "## Risk", "## Funding", "## Team", "## Competitive"]):
                capture = True
            if capture:
                relevant.append(line)
            if len("\n".join(relevant)) > max_chars:
                break
        return "\n".join(relevant)[:max_chars]

    old_summary = _extract_sections(old_run.report_markdown)
    new_summary = _extract_sections(new_run.report_markdown)

    already_found = [e.change_type for e in structural_event]

    prompt = f"""Compare these two due diligence reports for {new_run.company_name}.

OLD REPORT (from {old_run.created_at_display}):
{old_summary}

NEW REPORT (from {new_run.created_at_display}):
{new_summary}

Already detected changes: {already_found}

Identify any NEW significant changes NOT already in the list above.
Focus on: strategic shifts, new risks, product changes, partnership announcements.

Return a JSON array (empty [] if nothing new found):
[
  {{
    "change_type": "string — short snake_case label",
    "field": "string — which aspect changed",
    "old_value": "string",
    "new_value": "string",
    "severity": "high | medium | low",
    "description": "string — one sentence explanation"
  }}
]

Return ONLY the JSON array. No explanation, no markdown."""
    
    try:
        from tools.llm_factory import get_llm, call_llm_with_retry
        from langchain_core.messages import HumanMessage
        
        llm = get_llm(temperature=0.0)
        response = call_llm_with_retry(
            llm,
            [HumanMessage(content=prompt)],
            agent_name = "ChangeDetector",
            max_attempts=3,
        )

        text = response.content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])

        raw_list = json.loads(text)
        if not isinstance(raw_list, list):
            return []

        return [
            ChangeEvent(
                change_type=item.get("change_type", "unknown"),
                field=item.get("field", ""),
                old_value=item.get("old_value", ""),
                new_value=item.get("new_value", ""),
                severity=item.get("severity", "low"),
                description=item.get("description", ""),
            )
            for item in raw_list
            if isinstance(item, dict) and item.get("change_type")
        ]
    except Exception as e:
        print(f"  ⚠️  [ChangeDetector] LLM analysis skipped: {e}")
        return []


# ── Public interface ──────────────────────────────────────────────────────────

def detect_changes(new_run: ResearchRun, old_run: ResearchRun, use_llm: bool = True,) -> list[ChangeEvent]:
    """
    Detect all meaningful changes between two runs for the same company.

    Args:
        new_run:  The more recent run
        old_run:  The baseline run to compare against
        use_llm:  Whether to run LLM semantic analysis (default True)

    Returns:
        List of ChangeEvent objects sorted by severity (high → low).
    """
    print(f"  🔍 [ChangeDetector] Comparing runs: "
          f"{old_run.created_at_display} → {new_run.created_at_display}")
    
    # layer 1 : structural diff
    events = _structural_diff(new_run, old_run)
    print(f"  ✅ [ChangeDetector] Structural diff: {len(events)} changes found")

    # layer 2 : LLM semantic analysis
    if use_llm:
        llm_events = _llm_semantic_diff(new_run, old_run, events)
        events.extend(llm_events)
        print(f"  ✅ [ChangeDetector] LLM analysis: {len(llm_events)} additional changes")
    
    # sort: high -> medium -> low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    events.sort(key=lambda e: severity_order.get(e.severity, 3))

    print(f"  📊 [ChangeDetector] Total: {len(events)} changes "
          f"({sum(1 for e in events if e.severity == 'high')} high, "
          f"{sum(1 for e in events if e.severity == 'medium')} medium, "
          f"{sum(1 for e in events if e.severity == 'low')} low)")

    return events


def has_significant_changes(events: list[ChangeEvent]) -> bool:
    """Returns True if any change is high or medium severity — triggers alerts."""
    return any(e.severity in ("high", "medium") for e in events)