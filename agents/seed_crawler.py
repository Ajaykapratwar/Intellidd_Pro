"""
agents/seed_crawler.py — Stage 1: Seed Crawler Agent.

Scrapes the company homepage and extracts a structured company profile.
This runs FIRST — all other agents use company_name from this output.

Node name in graph: "seed_node"
Writes to state: seed_data, errors
"""

import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from pipeline.state import DDState
from prompts.agent_prompts import SEED_CRAWLER_PROMPT
from tools.llm_factory import get_llm_for_agent, call_llm_with_retry
from tools.scraper import scrape_url

AGENT_NAME = "SeedCrawler"

def _save_json(data: dict, output_dir: str, filename: str) -> None:
    """Save a dict as a JSON file in the run's output directory."""
    path = Path(output_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    
def _parse_llm_json(response_text: str, agent_name: str) -> dict:
    """
    Safely parse JSON from LLM response.
    Handles cases where the LLM wraps JSON in markdown code fences.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])     # remove first and last line
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[{agent_name}] JSON parse error: {e}")
        return {"error": f"JSON parse failed: {e}", "raw": response_text[:500]}


def run_seed_crawler(state: DDState) -> dict:
    """
    LangGraph node function for Stage 1.

    Args:
        state: Current DDState (reads: company_url, output_dir)

    Returns:
        Partial state update: {seed_data, errors}
    """
    company_url = state["company_url"]
    output_dir = state["output_dir"]
    errors = list(state.get("errors", []))

    print(f"\n{'='*60}")
    print(f"[{AGENT_NAME}] Starting seed crawl: {company_url}")
    print(f"{'='*60}")

    try:
        # Step 1: Scrape the company homepage
        scrape_result = scrape_url(company_url)

        if not scrape_result:
            error_msg = f"[{AGENT_NAME}] Failed to Scrape {company_url}: {scrape_result.error}"
            print(f"{error_msg}")
            errors.append(error_msg)

            # Return minimal profile so pipeline can continue

            fallback = {
                "company_name": company_url.split("//")[-1].split(".")[0].title(),
                "website": company_url,
                "description": "Could not scrape the website",
                "error": error_msg,
            }
            return {"seed_data": fallback, "errors": errors}
        
        print(f"Scraped {len(scrape_result.text)} chars via [{scrape_result.source}]")

        # Step 2: Extract structured profile via LLM
        llm = get_llm_for_agent(AGENT_NAME)
        prompt = SEED_CRAWLER_PROMPT.format(
            scraped_content = scrape_result.text[:8000],    # limit context
            company_url = company_url,
        )

        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)], AGENT_NAME)
        seed_data = _parse_llm_json(response.content, AGENT_NAME)

        # Step 3: Save to disk
        _save_json(seed_data, output_dir, "company_profile.json")

        company_name = seed_data.get("company_name", "Unknown Company")

        print(f"[{AGENT_NAME}] Extracted Profile for: {company_name}")

        return {"seed_data": seed_data, "errors": errors}
    
    except Exception as e:
        error_msg = f"[{AGENT_NAME}] Unexpected error: {str(e)}"
        print(f"{error_msg}")
        errors.append(error_msg)
        return {
            "seed_data": {"company_name": "Unknown", "website": company_url},
            "errors": errors,
        }
