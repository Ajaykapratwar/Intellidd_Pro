"""
pipeline/state.py — DDState: the shared data contract for the entire pipeline.

Every LangGraph node receives the full state and returns a partial update.
LangGraph merges the partial update back into the state automatically.

Usage:
    from pipeline.state import DDState
"""

from typing import TypedDict, Optional

class DDState(TypedDict):
    """
    The complete state object passed through every node in the LangGraph pipeline.

    Nodes only need to return the keys they modify — LangGraph
    merges updates automatically via reducer functions.
    """

    # Input
    company_url: str           # The URL the user submitted
    run_id: str                # UUID for this specific run (set by runner.py)
    output_dir: str            # Path to this run's output folder

    # Stage 1 : Seed Crawler Output
    seed_data: dict            # company_profile.json content

    # Stage 2 : Specialist Agent Output
    team_data: dict            # founders_team.json
    investor_data: dict        # investors.json
    press_data: dict           # press.json
    financials_data: dict      # financials.json
    tech_stack_data: dict      # tech_stack.json
    social_data: dict          # social.json

    # Stage 3 : Validation Output
    validation_notes: dict     # validation_notes.json

    # Stage 4 : Synthesis Output
    report_markdown: str       # The final report as a markdown string

    # Metadata
    pipeline_status: str       # "running" | "completed" | "failed"
    errors: list               # List of error strings from any agent
    start_time: float          # Unix timestamp of run start
    duration_seconds: float    # Total time taken


def initial_state(company_url: str, run_id: str, output_dir: str) -> DDState:
    """
    Returns a DDState with all required fields initialized to safe defaults.
    Call this in runner.py before invoking the graph.
    """

    import time
    return DDState(
        company_url=company_url,
        run_id=run_id,
        output_dir=output_dir,
        seed_data={},
        team_data={},
        investor_data={},
        press_data={},
        financials_data={},
        tech_stack_data={},
        social_data={},
        validation_notes={},
        report_markdown="",
        pipeline_status="running",
        errors=[],
        start_time=time.time(),
        duration_seconds=0.0
    )