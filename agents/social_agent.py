"""
agents/social_agent.py — Stage 2f: Social Media & Brand Research Agent.
"""

from pathlib import Path
import json
from langchain_core.messages import HumanMessage
from pipeline.state import DDState
from prompts.agent_prompts import SOCIAL_AGENT_PROMPT
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from tools.search import search_to_context
from prompts.sectors import detect_sector, get_sector_label
from prompts.sector_prompts import get_team_context

AGENT_NAME = "SocialAgent"

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
    
def run_social_agent(state: DDState) -> dict:
    """Research social media presence and brand strength."""
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    output_dir = state["output_dir"]

    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    print(f"[{AGENT_NAME}] Researching social for: {company_name}")

    try:
        research_data = "\n\n".join([
            search_to_context(f"{company_name} LinkedIn followers company page", max_results=4),
            search_to_context(f"{company_name} Twitter X social media following", max_results=4),
            search_to_context(f"{company_name} Product Hunt community Discord", max_results=3),
        ])

        llm = get_llm_for_agent(AGENT_NAME)
        prompt = SOCIAL_AGENT_PROMPT.format(
            company_name=company_name,
            sector_label=sector_label,
            sector_context=get_team_context(sector),
            research_data=research_data[:8000],
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        social_data = _parse_llm_json(response.content)

        _save_json(social_data, output_dir, "social.json")
        print(f"[{AGENT_NAME}] Done. Brand score: {social_data.get('overall_brand_score', 'N/A')}/10")

        return {"social_data": social_data}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"social_data": {"error": error_msg}}
