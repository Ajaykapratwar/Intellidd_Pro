"""
agents/competitor_agent.py — Stage 2g: Competitor Intelligence Agent.

Discovers and profiles 3-5 direct competitors for the target company, then produces a side-by-side comparison matrix and competitive positioning assessment.

Node name in graph: called inside "specialists_node" (parallel)
Writes to state: competitor_data
"""

import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from pipeline.state import DDState
from prompts.agent_prompts import COMPETITOR_AGENT_PROMPT
from prompts.sectors import detect_sector, get_sector_label
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from tools.scraper import scrape_url
from tools.search import search_to_context

AGENT_NAME = "CompetitorAgent"


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


def _discover_competitors(company_name: str, sector_label: str, llm) -> list[dict]:
    """
    Step 1: Discover competitor names + URLs via search, then use LLM to extract
    structured list of {name, website} dicts.
    Returns up to 5 competitors.
    """
    print(f"[{AGENT_NAME}] Discovering competitors for: {company_name}")

    search_context = "\n\n".join([
        search_to_context(f"{company_name} competitors alternatives", max_results=6),
        search_to_context(f"best alternatives to {company_name} {sector_label}", max_results=5),
    ])

    prompt = (
        f"From the search results below, extract the 3-5 most direct competitors to {company_name} ({sector_label}).\n"
        f"Return ONLY a JSON array of objects with 'name' and 'website' fields. Example:\n"
        f'[{{"name": "Acme Corp", "website": "https://acme.com"}}]\n\n'
        f"SEARCH RESULTS:\n{search_context[:4000]}"
    )
    response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
    result = _parse_llm_json(response.content)
    return result if isinstance(result, list) else []


def _scrape_competitor_basics(competitor_url: str) -> str:
    """
    Lightweight scrape of a competitor's homepage.
    Returns a short text summary (max 1500 chars).
    """
    result = scrape_url(competitor_url)
    if result and result.text:
        return result.text[:1500]
    return ""


def run_competitor_agent(state: DDState) -> dict:
    """
    Research competitor landscape for the target company.

    Args:
        state: Current DDState (reads: seed_data, company_url, output_dir)

    Returns:
        Partial state update: {competitor_data}
    """
    seed_data = state.get("seed_data", {})
    company_name = seed_data.get("company_name", "the company")
    company_url = state["company_url"]
    output_dir = state["output_dir"]

    # Detect sector for context-aware competitor research
    sector = detect_sector(seed_data)
    sector_label = get_sector_label(sector)

    # Build a short company summary for the prompt
    company_summary = (
        f"{seed_data.get('description', '')} | "
        f"Stage: {seed_data.get('stage', 'Unknown')} | "
        f"Business model: {seed_data.get('business_model', 'Unknown')} | "
        f"Products: {', '.join(seed_data.get('products_services', [])[:3])}"
    )

    print(f"[{AGENT_NAME}] Researching competitors for: {company_name} [{sector_label}]")

    try:
        llm = get_llm_for_agent(AGENT_NAME)

        # Step 1: Discover competitor names + URLs
        competitors = _discover_competitors(company_name, sector_label, llm)
        print(f"[{AGENT_NAME}] Discovered {len(competitors)} competitors to profile")

        # Step 2: Scrape each competitor's homepage
        competitor_scraped_parts = []
        for comp in competitors[:5]:
            website = comp.get("website", "")
            name = comp.get("name", "Unknown")
            if website:
                print(f"[{AGENT_NAME}] Scraping competitor: {name}")
                scraped = _scrape_competitor_basics(website)
                if scraped:
                    competitor_scraped_parts.append(f"### {name} ({website})\n{scraped}")
        competitor_scraped_data = "\n\n".join(competitor_scraped_parts) or "No competitor homepages scraped."

        # Step 3: Broad search context for the full matrix
        research_data = "\n\n".join([
            search_to_context(f"{company_name} competitors alternatives {sector_label}", max_results=6),
            search_to_context(f"best {sector_label} companies similar to {company_name}", max_results=5),
            search_to_context(f"{company_name} vs comparison review", max_results=4),
        ])

        # Step 4: LLM builds full competitor matrix using both search + scraped data
        prompt = COMPETITOR_AGENT_PROMPT.format(
            company_name=company_name,
            company_url=company_url,
            sector_label=sector_label,
            company_summary=company_summary,
            research_data=research_data[:6000],
            competitor_scraped_data=competitor_scraped_data[:4000],
        )
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        competitor_data = _parse_llm_json(response.content)

        # Step 3: Save to disk
        _save_json(competitor_data, output_dir, "competitor_intel.json")

        num_competitors = len(competitor_data.get("competitors", []))
        position = competitor_data.get("market_position", "Unknown")
        diff_score = competitor_data.get("differentiation_score", "N/A")

        print(
            f"[{AGENT_NAME}] Done. "
            f"Found {num_competitors} competitors | "
            f"Position: {position} | "
            f"Differentiation: {diff_score}/100"
        )

        return {"competitor_data": competitor_data}

    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Error: {str(e)}"
        print(f"{error_msg}")
        return {"competitor_data": {"error": error_msg}}