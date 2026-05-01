"""
agents/synthesis_agent.py — Stage 4: Report Synthesis Agent.

Takes all research + validation notes and generates the full Markdown report.

Node name in graph: "synthesis_node"
Writes to state: report_markdown, pipeline_status, duration_seconds
"""

import json
import time
from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage
from pipeline.state import DDState
from prompts.agent_prompts import SYNTHESIS_PROMPT
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from prompts.sectors import detect_sector, get_sector_label
from prompts.sector_prompts import get_team_context

AGENT_NAME = "Synthesis"


def run_synthesis(state: DDState) -> dict:
    """
    Generate the final due diligence report.

    Args:
        state: Full DDState with all research and validation data.

    Returns:
        Partial state update: {report_markdown, pipeline_status, duration_seconds}
    """
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    company_url = state["company_url"]
    output_dir = state["output_dir"]

    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    print(f"\n  📝 [{AGENT_NAME}] Writing final report for: {company_name}")

    all_research = {
        "company_profile": state.get("seed_data", {}),
        "team": state.get("team_data", {}),
        "investors": state.get("investor_data", {}),
        "press": state.get("press_data", {}),
        "financials": state.get("financials_data", {}),
        "tech_stack": state.get("tech_stack_data", {}),
        "social": state.get("social_data", {}),
    }

    try:
        llm = get_llm_for_agent(AGENT_NAME)
        prompt = SYNTHESIS_PROMPT.format(
            company_name=company_name,
            company_url=company_url,
            all_research_json=json.dumps(all_research, indent=2)[:10000],
            validation_json=json.dumps(state.get("validation_notes", {}), indent=2)[:3000],
            report_date=datetime.now().strftime("%B %d, %Y"),
            sector_label=sector_label,                    # ← ADD
            sector_context=get_team_context(sector),
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        report_markdown = response.content

        # Save report to disk
        report_path = Path(output_dir) / "report.md"
        report_path.write_text(report_markdown, encoding="utf-8")

        # Calculate total duration
        start_time = state.get("start_time", time.time())
        duration = round(time.time() - start_time, 1)

        print(f"[{AGENT_NAME}] Report saved: {report_path}")
        print(f"Total pipeline duration: {duration}s")
        print(f"\n{'='*60}")
        print(f"PIPELINE COMPLETE for {company_name}")
        print(f"📁 Outputs saved to: {output_dir}")
        print(f"{'='*60}\n")

        return {
            "report_markdown": report_markdown,
            "pipeline_status": "completed",
            "duration_seconds": duration,
        }

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {
            "report_markdown": f"# Report Generation Failed\n\nError: {error_msg}",
            "pipeline_status": "failed",
            "duration_seconds": round(time.time() - state.get("start_time", time.time()), 1),
        }