"""
agents/press_agent.py — Stage 2c: Press & Media Research Agent.
"""

from pathlib import Path
import json
from langchain_core.messages import HumanMessage
from pipeline.state import DDState
from prompts.agent_prompts import PRESS_AGENT_PROMPT
from tools.llm_factory import get_llm_for_agent
from tools.search import search_to_context

AGENT_NAME = "PressAgent"

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
    
def run_press_agent(state: DDState) -> dict:
    """Research press coverage and media sentiment."""
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    output_dir = state["output_dir"]

    print(f"[{AGENT_NAME}] Researching Press for: {company_name}")

    try:
        research_data = "\n\n".join([
            search_to_context(f"{company_name} news 2024 2025", max_results=6),
            search_to_context(f"{company_name} TechCrunch Forbes announcement", max_results=4),
            search_to_context(f"{company_name} press release launch", max_results=3),
        ])

        llm = get_llm_for_agent(AGENT_NAME)
        prompt = PRESS_AGENT_PROMPT.format(
            company_name=company_name,
            research_data=research_data[:8000],
        )
        response = llm.invoke([HumanMessage(content=prompt)])

        press_data = _parse_llm_json(response.content)

        _save_json(press_data, output_dir, "press.json")
        print(f"[{AGENT_NAME}] Done. Sentiment: {press_data.get('overall_sentiment', 'Unknown')}")

        return {"press_data": press_data}
    
    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"press_data": {"error": error_msg}}