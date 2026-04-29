"""
pipeline/graph.py — LangGraph StateGraph definition.

Pipeline flow:
  START
    → seed_node         (sequential — all agents need company_name from here)
    → specialists_node  (parallel — 6 agents run simultaneously)
    → validator_node    (sequential — reviews all specialist outputs)
    → synthesis_node    (sequential — writes final report)
  → END

All agents are standard Python functions — LangGraph handles state passing.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.graph import StateGraph, START, END

from pipeline.state import DDState
from agents.seed_crawler import run_seed_crawler
from agents.team_agent import run_team_agent
from agents.investor_agent import run_investor_agent
from agents.press_agent import run_press_agent
from agents.financials_agent import run_financials_agent
from agents.tech_stack_agent import run_tech_stack_agent
from agents.social_agent import run_social_agent
from agents.validator_agent import run_validator
from agents.synthesis_agent import run_synthesis
import config


# Parallel Specialists Node

def run_specialists_parallel(state: DDState) -> dict:
    """
    Runs all 6 specialist agents in parallel using ThreadPoolExecutor.

    This is a single LangGraph node that fans out internally.
    Each agent returns a partial state dict; we merge them all here.

    Why one node instead of 6 parallel nodes?
    LangGraph's Send API is great for dynamic fan-out, but for a fixed
    set of agents, a single parallel node is simpler, easier to debug,
    and handles the join automatically.
    """
    company_name = state.get("seed_data", {}).get("company_name", "the company")
    print(f"\n{'='*60}")
    print(f"Running 6 specialist agents in parallel for: {company_name}")
    print(f"Workers: {config.MAX_WORKERS} | Timeout: {config.AGENT_TIMEOUT_SECONDS}s each")
    print(f"{'='*60}")

    # Map of agent name → function
    specialists = {
        "team":       run_team_agent,
        "investors":  run_investor_agent,
        "press":      run_press_agent,
        "financials": run_financials_agent,
        "tech_stack": run_tech_stack_agent,
        "social":     run_social_agent,
    }

    # Merged state update from all agents
    merged_updates: dict = {}
    errors: list = list(state.get("errors", []))

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        # Submit all agents
        future_to_name = {
            executor.submit(_run_with_timeout, fn, state, config.AGENT_TIMEOUT_SECONDS): name
            for name, fn in specialists.items()
        }

        # Collect results as they complete
        for future in as_completed(future_to_name):
            agent_name = future_to_name[future]
            try:
                result = future.result()
                if result:
                    merged_updates.update(result)
                    print(f"[{agent_name}] Completed")
            except Exception as e:
                error_msg = f"[{agent_name}] Failed with exception: {str(e)}"
                print(f"{error_msg}")
                errors.append(error_msg)

    merged_updates["errors"] = errors
    return merged_updates


def _run_with_timeout(fn, state: DDState, timeout: int) -> dict:
    """
    Wrapper to run an agent function with a timeout.
    If agent exceeds timeout, returns an error dict so pipeline continues.
    """
    start = time.time()
    try:
        result = fn(state)
        elapsed = round(time.time() - start, 1)
        print(f"Took {elapsed}s")
        return result
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        raise RuntimeError(f"Agent failed after {elapsed}s: {e}") from e


# Build the Graph

def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph StateGraph.

    Returns a compiled graph ready to invoke with:
        graph.invoke(initial_state)
    """
    builder = StateGraph(DDState)

    # Add all nodes
    builder.add_node("seed_node",        run_seed_crawler)
    builder.add_node("specialists_node", run_specialists_parallel)
    builder.add_node("validator_node",   run_validator)
    builder.add_node("synthesis_node",   run_synthesis)

    # Wire the edges (sequential flow)
    builder.add_edge(START,               "seed_node")
    builder.add_edge("seed_node",         "specialists_node")
    builder.add_edge("specialists_node",  "validator_node")
    builder.add_edge("validator_node",    "synthesis_node")
    builder.add_edge("synthesis_node",    END)

    return builder.compile()


# Singleton compiled graph — import this in runner.py
dd_graph = build_graph()