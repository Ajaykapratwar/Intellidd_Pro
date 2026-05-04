"""
agents/risk_scorer.py — Stage 3b: Quantitative Risk Scoring Engine.

Runs AFTER the validator. Analyzes all research data and produces
a structured risk scorecard across 5 investment dimensions:
  1. Founder Risk
  2. Market Risk
  3. Financial Risk
  4. Technical Risk
  5. Reputational Risk

Also produces an overall DD Confidence Score (0-100).

Node name in graph: "risk_node"
Writes to state: risk_scorecard
"""

import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from pipeline.state import DDState
from prompts.agent_prompts import RISK_SCORER_PROMPT
from prompts.sectors import detect_sector, get_sector_label
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry

AGENT_NAME = "RiskScorer"

# Risk severity thresholds
SEVERITY_MAP = {
    (1, 3): "Low",
    (4, 6): "Medium",
    (7, 9): "High",
    (10, 10): "Critical",
}

# Color codes for terminal output
SEVERITY_COLORS = {
    "Low": "✅",
    "Medium": "⚠️ ",
    "High": "🔴",
    "Critical": "💀",
}


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


def _get_severity_label(score: int) -> str:
    """Convert numeric score to severity label."""
    for (low, high), label in SEVERITY_MAP.items():
        if low <= score <= high:
            return label
    return "Unknown"


def _print_scorecard_summary(scorecard: dict, company_name: str) -> None:
    """Pretty-print the risk scorecard to terminal."""
    dimensions = [
        ("founder_risk",      "Founder Risk    "),
        ("market_risk",       "Market Risk     "),
        ("financial_risk",    "Financial Risk  "),
        ("technical_risk",    "Technical Risk  "),
        ("reputational_risk", "Reputational Risk"),
    ]
    print(f"\n[{AGENT_NAME}] Risk Scorecard for: {company_name}")
    print(f"  {'─'*50}")
    for key, label in dimensions:
        dim = scorecard.get(key, {})
        score = dim.get("score", "?")
        severity = dim.get("severity", _get_severity_label(int(score) if str(score).isdigit() else 5))
        icon = SEVERITY_COLORS.get(severity, "❓")
        print(f"  {icon} {label}: {score}/10  [{severity}]")
    print(f"  {'─'*50}")
    overall = scorecard.get("overall_risk_score", "?")
    confidence = scorecard.get("dd_confidence_score", "?")
    print(f"Overall Risk Score  : {overall}/10")
    print(f"DD Confidence Score : {confidence}/100")
    print(f"  {'─'*50}")


def run_risk_scorer(state: DDState) -> dict:
    """
    Generate quantitative risk scorecard from all research data.

    Runs after validator_node. Reads all specialist outputs + validation
    and produces risk scores across 5 dimensions.

    Args:
        state: Full DDState with all research populated.

    Returns:
        Partial state update: {risk_scorecard}
    """
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    output_dir = state["output_dir"]

    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    print(f"\n[{AGENT_NAME}] Scoring risk dimensions for: {company_name} [{sector_label}]")

    # Compile all research into one payload for the LLM
    all_research = {
        "company_profile":  state.get("seed_data", {}),
        "team":             state.get("team_data", {}),
        "investors":        state.get("investor_data", {}),
        "press":            state.get("press_data", {}),
        "financials":       state.get("financials_data", {}),
        "tech_stack":       state.get("tech_stack_data", {}),
        "social":           state.get("social_data", {}),
        "competitors":      state.get("competitor_data", {}),
    }

    try:
        llm = get_llm_for_agent(AGENT_NAME)
        prompt = RISK_SCORER_PROMPT.format(
            company_name=company_name,
            sector_label=sector_label,
            all_research_json=json.dumps(all_research, indent=2)[:10000],
            validation_json=json.dumps(state.get("validation_notes", {}), indent=2)[:3000],
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        risk_scorecard = _parse_llm_json(response.content)

        # Ensure severity labels are set (in case LLM omitted them)
        for dim in ["founder_risk", "market_risk", "financial_risk",
                    "technical_risk", "reputational_risk"]:
            if dim in risk_scorecard:
                score = risk_scorecard[dim].get("score", 5)
                if not risk_scorecard[dim].get("severity"):
                    risk_scorecard[dim]["severity"] = _get_severity_label(
                        int(score) if str(score).isdigit() else 5
                    )

        # Save to disk
        _save_json(risk_scorecard, output_dir, "risk_scorecard.json")

        # Print pretty summary
        _print_scorecard_summary(risk_scorecard, company_name)

        return {"risk_scorecard": risk_scorecard}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        # Return a default scorecard so pipeline doesn't break
        return {
            "risk_scorecard": {
                "error": error_msg,
                "overall_risk_score": 5,
                "dd_confidence_score": 30,
            }
        }