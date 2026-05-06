"""
agents/financials_agent.py — Stage 2d: Financial Signals Research Agent.
"""

from pathlib import Path
import json
from langchain_core.messages import HumanMessage
from pipeline.state import DDState
from prompts.agent_prompts import FINANCIALS_AGENT_PROMPT
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from tools.search import search_to_context
from prompts.sectors import detect_sector, get_sector_label
from prompts.sector_prompts import get_team_context

AGENT_NAME = "FinancialsAgent"

def _save_json(data: dict, output_dir: str, filename: str) -> None:
    path = Path(output_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _parse_llm_json(response_text: str) -> dict:
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": response_text[:500]}
    
def run_financials_agent(state: DDState) -> dict:
    """Research financial signals and business model economics."""
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    company_url = state["company_url"]
    output_dir = state["output_dir"]

    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    print(f"[{AGENT_NAME}] Researching financial for: {company_name}")

    try:
        research_data = "\n\n".join([
            search_to_context(f"{company_name} funding rounds", max_results=5),
            search_to_context(f"{company_name} revenue ARR MRR", max_results=4),
            search_to_context(f"{company_name} customer testimonials case studies", max_results=3),
            search_to_context(f"{company_name} job postings finance", max_results=3),
            search_to_context(f"{company_name} revenue ARR growth customers", max_results=5),
            search_to_context(f"{company_name} CEO interview revenue metrics", max_results=4),
        ])

        llm = get_llm_for_agent(AGENT_NAME)
        prompt = FINANCIALS_AGENT_PROMPT.format(
            company_name=company_name,
            company_url=company_url,
            sector_label=sector_label,
            sector_context=get_team_context(sector),
            research_data=research_data[:8000],
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        financials_data = _parse_llm_json(response.content)

        _save_json(financials_data, output_dir, "financials.json")
        print(f"[{AGENT_NAME}] Done. Revenue estimate: {financials_data.get('revenue_estimate', 'Unknown')}")

        return {"financials_data": financials_data}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"financials_data": {"error": error_msg}}
