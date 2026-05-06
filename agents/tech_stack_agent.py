"""
agents/tech_stack_agent.py — Stage 2e: Technology Stack Research Agent.
"""

from pathlib import Path
import json
from langchain_core.messages import HumanMessage
from pipeline.state import DDState
from prompts.agent_prompts import TECH_STACK_AGENT_PROMPT
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from tools.search import search_to_context
from tools.scraper import scrape_url
from prompts.sectors import detect_sector, get_sector_label
from prompts.sector_prompts import get_team_context

AGENT_NAME = "TechStackAgent"

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
    
def run_tech_stack_agent(state: DDState) -> dict:
    """Research technology stack, infrastructure, and engineering quality."""
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    company_url = state["company_url"]
    output_dir = state["output_dir"]

    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    print(f"[{AGENT_NAME}] Researching tech stack for: {company_name}")

    try:
        search_context = "\n\n".join([
            search_to_context(f"{company_name} software engineer jobs Python React AWS", max_results=5),
            search_to_context(f"{company_name} engineering blog tech stack infrastructure", max_results=4),
            search_to_context(f"{company_name} github open source", max_results=3),
        ])

        # Try scraping careers page for job postings
        careers_text = ""
        for path in ["/careers", "/jobs", "/engineering"]:
            careers_url = company_url.rstrip("/") + path
            result = scrape_url(careers_url)
            if result and len(result.text) > 200:
                careers_text = f"\n\nCAREERS PAGE:\n{result.text[:3000]}"
                break

        research_data = search_context + careers_text

        llm = get_llm_for_agent(AGENT_NAME)
        prompt = TECH_STACK_AGENT_PROMPT.format(
            company_name=company_name,
            company_url=company_url,
            sector_label=sector_label,
            sector_context=get_team_context(sector),
            research_data=research_data[:8000],
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        tech_data = _parse_llm_json(response.content)

        _save_json(tech_data, output_dir, "tech_stack.json")
        score = tech_data.get("tech_stack_modernity_score", "N/A")
        print(f"[{AGENT_NAME}] Done. Modernity score: {score}/10")

        return {"tech_stack_data": tech_data}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"tech_stack_data": {"error": error_msg}}
