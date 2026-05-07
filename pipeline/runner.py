"""
pipeline/runner.py — Public entry point for the DD pipeline.

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

from langchain_core.runnables.config import RunnableConfig

from pipeline.graph import dd_graph
from pipeline.state import initial_state, DDState
from persistence.db import init_db
from persistence.queries import save_run
from tools.observability import get_langsmith_trace_url, build_performance_summary, check_langsmith_config
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
    ls_run_id = str(uuid.uuid4())
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

    ls_config = check_langsmith_config()

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

    # ── Build LangGraph RunnableConfig for LangSmith tracking ─────────────────
    # Passing the ls_run_id here tells LangSmith to record this run
    # under that specific UUID — which we then use to fetch the trace URL
    graph_config = RunnableConfig(
        run_id=ls_run_id,
        run_name=f"IntelliDD-{company_slug}-{run_id}",
        tags=["intellidd-pro", company_slug],
        metadata={
            "company_url":  company_url,
            "company_slug": company_slug,
            "intellidd_run_id": run_id,
        },
    )

    # ── Run the graph ─────────────────────────────────────────────────────────
    import time
    pipeline_start = time.time()

    final_state = dd_graph.invoke(state, config=graph_config)

    total_duration = round(time.time() - pipeline_start, 1)

    # ── Phase 6: Capture LangSmith trace URL ─────────────────────────────────
    trace_url = ""
    if ls_config["enabled"]:
        print(f"\n  🔭 [Observability] Fetching LangSmith trace URL...")
        trace_url = get_langsmith_trace_url(ls_run_id) or ""

    # ── Phase 6: Build performance summary ────────────────────────────────────
    raw_timings   = final_state.get("performance_stats", {}).get("agent_timings", {})
    uploaded_count = len(uploaded_files or [])

    performance_stats = build_performance_summary(
        agent_timings=raw_timings,
        total_duration=total_duration,
        trace_url=trace_url,
        model_used=config.GROQ_MODEL,
        docs_uploaded=uploaded_count,
    )

    # Write back to final_state for UI consumption
    final_state["performance_stats"]   = performance_stats
    final_state["langsmith_trace_url"] = trace_url
    final_state["run_id"]              = run_id
    final_state["output_dir"]          = output_dir
    final_state["uploaded_files"]      = uploaded_files or []
    final_state["duration_seconds"]    = total_duration

    saved = save_run(final_state)
    if saved:
        print(f"  💾 Run saved to database (run_id: {run_id})")
    else:
        print(f"  ⚠️  Failed to save run to database — check logs")
    # ─────────────────────────────────────────────────────────────────────────

    # ── Print performance summary ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  ✅ PIPELINE COMPLETE — {company_slug.title()}")
    print(f"  ⏱  Total time: {total_duration}s")
    print(f"  🧠 Agents: {performance_stats.get('agent_count', 0)}")
    print(f"  🔤 Tokens (est.): ~{performance_stats.get('total_tokens_est', 0):,}")
    print(f"  ⚡ Parallel saved: {performance_stats.get('parallel_time_saved_seconds', 0)}s")
    if trace_url:
        print(f"  🔭 LangSmith: {trace_url}")
    print(f"{'='*60}\n")

    return final_state


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python pipeline/runner.py <company_url>")
        print("Example: uv run python pipeline/runner.py https://stripe.com")
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
    trace = result.get("langsmith_trace_url", "")
    if trace:
        print(f"LangSmith trace: {trace}")