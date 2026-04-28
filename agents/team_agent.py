"""
agents/team_agent.py — Stage 2a: Team & Leadership Research Agent.

Researches founders, executives, advisors, and hiring signals.

Node name in graph: called inside "specialists_node" (parallel)
Writes to state: team_data
"""

import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from pipeline.state import DDState
from prompts.agent_prompts import TEAM_AGENT_PROMPT
from tools.llm_factory import get_llm_for_agent
from tools.scraper import scrape_url
from tools.search import search_to_context

AGENT_NAME = "TeamAgent"


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


def run_team_agent(state: DDState) -> dict:
    """
    Research team and leadership. Called in parallel with other specialist agents.

    Args:
        state: Current DDState (reads: seed_data, company_url, output_dir)

    Returns:
        Partial state update: {team_data}
    """
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    company_url = state["company_url"]
    output_dir = state["output_dir"]

    print(f"[{AGENT_NAME}] Researching team for: {company_name}")

    try:
        # Step 1: Multi-angle search
        search_context = "\n\n".join([
            search_to_context(f"{company_name} founders CEO leadership team", max_results=5),
            search_to_context(f"{company_name} co-founder background experience", max_results=4),
            search_to_context(f"{company_name} hiring jobs careers", max_results=3),
        ])

        # Step 2: Scrape About/Team page if it exists
        about_text = ""
        for path in ["/about", "/team", "/about-us"]:
            about_url = company_url.rstrip("/") + path
            result = scrape_url(about_url)
            if result and len(result.text) > 200:
                about_text = f"\n\nABOUT PAGE ({about_url}):\n{result.text[:3000]}"
                break

        research_data = search_context + about_text

        # Step 3: LLM extraction
        llm = get_llm_for_agent(AGENT_NAME)
        prompt = TEAM_AGENT_PROMPT.format(
            company_name=company_name,
            company_url=company_url,
            research_data=research_data[:8000],
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        team_data = _parse_llm_json(response.content)

        _save_json(team_data, output_dir, "founders_team.json")
        print(f"[{AGENT_NAME}] Done. Found {len(team_data.get('founders', []))} founder(s).")

        return {"team_data": team_data}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"team_data": {"error": error_msg}}