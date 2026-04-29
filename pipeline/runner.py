"""
pipeline/runner.py — Public entry point for the DD pipeline.

Usage:
    from pipeline.runner import run_due_diligence
    result = run_due_diligence("https://stripe.com")
    print(result["report_markdown"])

Also runnable directly for testing:
    uv run python pipeline/runner.py https://stripe.com
"""

import sys
import uuid
from datetime import datetime
from pathlib import Path

from pipeline.graph import dd_graph
from pipeline.state import initial_state, DDState
import config


def run_due_diligence(company_url: str) -> DDState:
    """
    Run the full due diligence pipeline on a company URL.

    Args:
        company_url: The company's website URL (e.g. "https://stripe.com")

    Returns:
        The final DDState with all research data and report_markdown populated.
    """
    # Validate config at runtime
    warnings = config.validate_config()
    for w in warnings:
        print(w)

    # Create unique run ID and output directory
    run_id = str(uuid.uuid4())[:8]  # short 8-char ID for readability
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Derive a safe company slug from URL for folder naming
    company_slug = (
        company_url
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
        .split(".")[0]
        .lower()
    )
    output_dir = str(
        Path(config.OUTPUTS_DIR) / f"{company_slug}_{timestamp}_{run_id}"
    )
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"IntelliDD Pro — Due Diligence Pipeline")
    print(f"{'='*60}")
    print(f"  Company URL : {company_url}")
    print(f"  Run ID      : {run_id}")
    print(f"  Output Dir  : {output_dir}")
    print(f"  LangSmith   : {'enabled' if config.LANGCHAIN_TRACING_V2 else 'disabled'}")
    print(f"{'='*60}\n")

    # Build initial state
    state = initial_state(
        company_url=company_url,
        run_id=run_id,
        output_dir=output_dir,
    )

    # Run the graph — this blocks until all 4 stages complete
    final_state = dd_graph.invoke(state)

    return final_state


if __name__ == "__main__":
    # CLI usage: uv run python pipeline/runner.py https://stripe.com
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
    print(f"\nFull report saved to: {result['output_dir']}/report.md")
    print(f"Pipeline status: {result['pipeline_status']}")
    print(f"Errors: {result['errors'] or 'None'}")