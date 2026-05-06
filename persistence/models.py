"""
persistence/models.py — Dataclass models for database records.

These map 1:1 to database rows but as typed Python objects.
All query functions return these instead of raw sqlite3.Row.

Usage:
    from persistence.models import ResearchRun
    run = ResearchRun.from_row(sqlite_row)
    print(run.company_name, run.overall_risk_score)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ResearchRun:
    """
    Represents one complete due diligence pipeline run.
    Maps to the research_runs table.
    """
    # Identity
    run_id:          str
    company_name:    str
    company_url:     str
    company_slug:    str

    # Timing
    created_at:      str        # ISO 8601 string
    duration_seconds: float

    # Status
    pipeline_status:  str
    sector_detected:  str
    errors:           list = field(default_factory=list)

    # Research data (parsed from JSON)
    seed_data:        dict = field(default_factory=dict)
    team_data:        dict = field(default_factory=dict)
    investor_data:    dict = field(default_factory=dict)
    press_data:       dict = field(default_factory=dict)
    financials_data:  dict = field(default_factory=dict)
    tech_stack_data:  dict = field(default_factory=dict)
    social_data:      dict = field(default_factory=dict)
    competitor_data:  dict = field(default_factory=dict)
    validation_notes: dict = field(default_factory=dict)
    risk_scorecard:   dict = field(default_factory=dict)

    # Final outputs
    report_markdown:  str = ""
    output_dir:       str = ""

    # RAG
    documents_uploaded: int = 0
    doc_names:          list = field(default_factory=list)

    # Observability
    langsmith_trace_url: str = ""

    # User metadata
    notes:      str = ""
    is_starred: bool = False
    tags:       list = field(default_factory=list)

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def overall_risk_score(self) -> Optional[int]:
        """Shortcut to risk scorecard's overall score."""
        val = self.risk_scorecard.get("overall_risk_score")
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def dd_confidence_score(self) -> Optional[int]:
        """Shortcut to DD confidence score."""
        val = self.risk_scorecard.get("dd_confidence_score")
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    @property
    def total_funding(self) -> str:
        """Shortcut to total funding from investor data."""
        return self.investor_data.get("total_funding_usd", "Unknown")

    @property
    def market_position(self) -> str:
        """Shortcut to market position from competitor data."""
        return self.competitor_data.get("market_position", "Unknown")

    @property
    def created_at_display(self) -> str:
        """Human-readable timestamp."""
        try:
            dt = datetime.fromisoformat(self.created_at)
            return dt.strftime("%b %d, %Y at %I:%M %p")
        except Exception:
            return self.created_at

    @property
    def duration_display(self) -> str:
        """Human-readable duration."""
        s = self.duration_seconds
        if s < 60:
            return f"{int(s)}s"
        return f"{int(s // 60)}m {int(s % 60)}s"

    @property
    def has_documents(self) -> bool:
        return self.documents_uploaded > 0

    @property
    def is_complete(self) -> bool:
        return self.pipeline_status == "completed"

    # ── Factory method ────────────────────────────────────────────────────────

    @classmethod
    def from_row(cls, row: dict, tags: list[str] | None = None) -> "ResearchRun":
        """
        Create a ResearchRun from a sqlite3.Row or dict.

        Args:
            row:  A sqlite3.Row (or dict) from the research_runs table
            tags: Optional list of tag strings for this run
        """
        def safe_json(val, default):
            if not val:
                return default
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return default

        return cls(
            run_id=row["run_id"],
            company_name=row["company_name"],
            company_url=row["company_url"],
            company_slug=row["company_slug"],
            created_at=row["created_at"],
            duration_seconds=float(row["duration_seconds"] or 0),
            pipeline_status=row["pipeline_status"] or "unknown",
            sector_detected=row["sector_detected"] or "",
            errors=safe_json(row["errors_json"], []),
            seed_data=safe_json(row["seed_data_json"], {}),
            team_data=safe_json(row["team_data_json"], {}),
            investor_data=safe_json(row["investor_data_json"], {}),
            press_data=safe_json(row["press_data_json"], {}),
            financials_data=safe_json(row["financials_data_json"], {}),
            tech_stack_data=safe_json(row["tech_stack_data_json"], {}),
            social_data=safe_json(row["social_data_json"], {}),
            competitor_data=safe_json(row["competitor_data_json"], {}),
            validation_notes=safe_json(row["validation_notes_json"], {}),
            risk_scorecard=safe_json(row["risk_scorecard_json"], {}),
            report_markdown=row["report_markdown"] or "",
            output_dir=row["output_dir"] or "",
            documents_uploaded=int(row["documents_uploaded"] or 0),
            doc_names=safe_json(row["doc_names_json"], []),
            langsmith_trace_url=row["langsmith_trace_url"] or "",
            notes=row["notes"] or "",
            is_starred=bool(row["is_starred"]),
            tags=tags or [],
        )

    def to_summary_dict(self) -> dict:
        """
        Returns a lightweight summary dict for display in lists/tables.
        Does NOT include heavy fields like report_markdown or full JSON data.
        """
        return {
            "run_id":              self.run_id,
            "company_name":        self.company_name,
            "company_url":         self.company_url,
            "sector":              self.sector_detected,
            "created_at":          self.created_at_display,
            "duration":            self.duration_display,
            "status":              self.pipeline_status,
            "risk_score":          f"{self.overall_risk_score}/10" if self.overall_risk_score else "N/A",
            "confidence":          f"{self.dd_confidence_score}/100" if self.dd_confidence_score else "N/A",
            "funding":             self.total_funding,
            "market_position":     self.market_position,
            "has_docs":            "📄" if self.has_documents else "—",
            "starred":             "⭐" if self.is_starred else "—",
        }