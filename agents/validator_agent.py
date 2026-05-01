"""
agents/validator_agent.py — Stage 3: Validation & QA Agent.

Reviews all specialist outputs together and:
- Identifies contradictions between data sources
- Flags critical missing information
- Notes low-confidence findings
- Highlights the most important signals

Node name in graph: "validator_node"
Writes to state: validation_notes
"""

from pathlib import Path
import json
from langchain_core.messages import HumanMessage
from pipeline.state import DDState
from prompts.agent_prompts import VALIDATOR_PROMPT
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from tools.search import search_to_context
from tools.scraper import scrape_url
from prompts.sectors import detect_sector, get_sector_label
from prompts.sector_prompts import get_team_context

AGENT_NAME = "Validator"

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
    
def run_validator(state: DDState) -> dict:
    """
    Validate all specialist outputs for consistency and completeness.

    Args:
        state: Full DDState with all specialist results populated.

    Returns:
        Partial state update: {validation_notes}
    """
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    output_dir = state["output_dir"]

    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    print(f"[{AGENT_NAME}] Validating all research for: {company_name}")

    # Collect all specialist outputs into one dict for the LLM
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
        prompt = VALIDATOR_PROMPT.format(
            company_name=company_name,
            sector_label=sector_label,                    # ← ADD
            sector_context=get_team_context(sector),      
            all_research_json=json.dumps(all_research, indent=2)[:10000],
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        validation_notes  = _parse_llm_json(response.content)

        _save_json(validation_notes , output_dir, "social.json")

        quality = validation_notes.get("overall_data_quality", "N/A")
        gaps = len(validation_notes.get("critical_gaps", []))
        print(f"[{AGENT_NAME}] Done. Data quality: {quality}/10 | Gaps found: {gaps}")

        return {"validation_notes": validation_notes}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"validation_notes": {"error": error_msg}}
