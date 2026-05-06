"""
pipeline/runner.py — Public entry point for the DD pipeline.
Updated for Phase 4: saves every completed run to SQLite automatically.

Usage:
    from pipeline.runner import run_due_diligence
    result = run_due_diligence("https://stripe.com")

CLI:
    uv run python pipeline/runner.py https://stripe.com
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

from pipeline.graph import dd_graph
from pipeline.state import initial_state, DDState
from persistence.db import init_db
from persistence.queries import save_run
import config


def run_due_diligence(company_url: str, uploaded_files: list | None = None,) -> DDState:
    """
    Run the full due diligence pipeline on a company URL.

    Args:
        company_url:     The company's website URL
        uploaded_files:  Optional list of file paths for RAG

    Returns:
        The final DDState with all research data populated.
    """
    # Validate config
    warnings = config.validate_config()
    for w in warnings:
        print(w)

    # Ensure DB is initialized
    init_db()

    # Create unique run ID and output directory
    run_id    = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    company_slug = (
        company_url
        .replace("https://", "").replace("http://", "")
        .replace("www.", "").split("/")[0].split(".")[0].lower()
    )
    output_dir = str(
        Path(config.OUTPUTS_DIR) / f"{company_slug}_{timestamp}_{run_id}"
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  🧠 IntelliDD Pro — Due Diligence Pipeline")
    print(f"{'='*60}")
    print(f"  Company URL : {company_url}")
    print(f"  Run ID      : {run_id}")
    print(f"  Output Dir  : {output_dir}")
    print(f"  Documents   : {len(uploaded_files or [])} file(s)")
    print(f"  LangSmith   : {'enabled' if config.LANGCHAIN_TRACING_V2 else 'disabled'}")
    print(f"{'='*60}\n")

    # Build initial state
    state = initial_state(
        company_url=company_url,
        run_id=run_id,
        output_dir=output_dir,
        uploaded_files=uploaded_files or [],
    )

    # Run the graph
    final_state = dd_graph.invoke(state)

    # ── Phase 4: Save to SQLite ───────────────────────────────────────────────
    # Add run_id and output_dir to final_state so save_run() can access them
    final_state["run_id"]       = run_id
    final_state["output_dir"]   = output_dir
    final_state["uploaded_files"] = uploaded_files or []
    saved = save_run(final_state)
    if saved:
        print(f"  💾 Run saved to database (run_id: {run_id})")
    else:
        print(f"  ⚠️  Failed to save run to database — check logs")
    # ─────────────────────────────────────────────────────────────────────────

    return final_state


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python pipeline/runner.py <company_url>")
        sys.exit(1)

    url = sys.argv[1]
    result = run_due_diligence(url)

    print("\n" + "="*60)
    print("REPORT PREVIEW (first 500 chars):")
    print("="*60)
    print(result["report_markdown"][:500])
    print("...")
    print(f"\nFull report: {result['output_dir']}/report.md")
    print(f"Pipeline status: {result['pipeline_status']}")
    print(f"DB saved: {config.DB_PATH}")