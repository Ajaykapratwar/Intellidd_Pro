"""
pipeline/state.py — DDState: the shared data contract for the entire pipeline.
Updated for Phase 3: adds RAG fields (chroma_collection_id, doc_context, uploaded_files).
"""

from typing import TypedDict, Optional


class DDState(TypedDict):
    # ── Input ─────────────────────────────────────────────────────────────────
    company_url:    str
    run_id:         str
    output_dir:     str
    uploaded_files: list   # ← NEW (Phase 3): list of uploaded file paths

    # ── Stage 1: Seed Crawler ─────────────────────────────────────────────────
    seed_data: dict

    # ── Stage 2: Specialist Agents (parallel) ─────────────────────────────────
    team_data:       dict
    investor_data:   dict
    press_data:      dict
    financials_data: dict
    tech_stack_data: dict
    social_data:     dict
    competitor_data: dict

    # ── Stage 3: Validation + Risk + RAG ──────────────────────────────────────
    validation_notes:      dict
    risk_scorecard:        dict
    chroma_collection_id:  str   # ← NEW (Phase 3): run_id of ChromaDB collection
    doc_context:           str   # ← NEW (Phase 3): formatted doc excerpts for synthesis

    # ── Stage 4: Synthesis ────────────────────────────────────────────────────
    report_markdown: str

    # ── Metadata ──────────────────────────────────────────────────────────────
    pipeline_status:  str
    errors:           list
    start_time:       float
    duration_seconds: float


def initial_state(
    company_url:    str,
    run_id:         str,
    output_dir:     str,
    uploaded_files: list | None = None,
) -> DDState:
    """Returns a DDState with all fields initialized to safe defaults."""
    import time
    return DDState(
        company_url=company_url,
        run_id=run_id,
        output_dir=output_dir,
        uploaded_files=uploaded_files or [],   # ← NEW
        seed_data={},
        team_data={},
        investor_data={},
        press_data={},
        financials_data={},
        tech_stack_data={},
        social_data={},
        competitor_data={},
        validation_notes={},
        risk_scorecard={},
        chroma_collection_id="",               # ← NEW
        doc_context="",                        # ← NEW
        report_markdown="",
        pipeline_status="running",
        errors=[],
        start_time=time.time(),
        duration_seconds=0.0,
    )