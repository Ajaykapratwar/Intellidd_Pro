"""
pipeline/graph.py — LangGraph StateGraph definition.
Updated for Phase 3: adds doc_ingest_node and rag_node.

Pipeline flow:
  START
    → seed_node
    → doc_ingest_node
    → specialists_node  (7 agents in parallel)
    → validator_node
    → risk_node
    → rag_node
    → synthesis_node
  → END
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from langgraph.graph import StateGraph, START, END

from pipeline.state import DDState
from agents.seed_crawler import run_seed_crawler
from agents.team_agent import run_team_agent
from agents.investor_agent import run_investor_agent
from agents.press_agent import run_press_agent
from agents.financials_agent import run_financials_agent
from agents.tech_stack_agent import run_tech_stack_agent
from agents.social_agent import run_social_agent
from agents.competitor_agent import run_competitor_agent
from agents.validator_agent import run_validator
from agents.risk_scorer import run_risk_scorer
from agents.rag_agent import run_rag_agent           # ← NEW
from agents.synthesis_agent import run_synthesis
import config


# Phase 3: Document Ingestion Node

def run_doc_ingest(state: DDState) -> dict:
    """
    Process uploaded documents into ChromaDB.

    Runs after seed_node so we have the run_id established.
    If no files were uploaded, this is a silent no-op.

    Node name: "doc_ingest_node"
    Writes to state: chroma_collection_id
    """
    uploaded_files = state.get("uploaded_files", [])
    run_id = state["run_id"]

    if not uploaded_files:
        return {"chroma_collection_id": ""}

    print(f"\n  📁 [DocIngest] Processing {len(uploaded_files)} uploaded file(s)...")

    try:
        from rag.document_processor import process_document, get_document_summary
        from rag.vector_store import VectorStore

        vs = VectorStore(run_id=run_id)
        total_chunks = 0

        for file_path in uploaded_files:
            try:
                chunks = process_document(file_path)
                if chunks:
                    added = vs.add_chunks(chunks)
                    total_chunks += added
                    print(f"  ✅ [DocIngest] {get_document_summary(chunks)}")
            except Exception as e:
                print(f"  ⚠️  [DocIngest] Failed to process {file_path}: {e}")

        if total_chunks > 0:
            print(f"  ✅ [DocIngest] Total: {total_chunks} chunks stored in ChromaDB")
            return {"chroma_collection_id": run_id}
        else:
            print(f"  ⚠️  [DocIngest] No chunks extracted from uploaded files")
            return {"chroma_collection_id": ""}

    except Exception as e:
        print(f"  ❌ [DocIngest] Error: {e}")
        return {"chroma_collection_id": ""}


# Parallel Specialists Node

def run_specialists_parallel(state: DDState) -> dict:
    """Runs all 7 specialist agents in parallel."""
    company_name = state.get("seed_data", {}).get("company_name", "the company")
    print(f"\n{'='*60}")
    print(f"  Running 7 specialist agents in parallel for: {company_name}")
    print(f"  Workers: {config.MAX_WORKERS} | Timeout: {config.AGENT_TIMEOUT_SECONDS}s each")
    print(f"{'='*60}")

    specialists = {
        "team":        run_team_agent,
        "investors":   run_investor_agent,
        "press":       run_press_agent,
        "financials":  run_financials_agent,
        "tech_stack":  run_tech_stack_agent,
        "social":      run_social_agent,
        "competitors": run_competitor_agent,
    }

    merged_updates: dict = {}
    errors: list = list(state.get("errors", []))

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        future_to_name = {
            executor.submit(_run_with_timeout, fn, state, config.AGENT_TIMEOUT_SECONDS): name
            for name, fn in specialists.items()
        }
        for future in as_completed(future_to_name):
            agent_name = future_to_name[future]
            try:
                result = future.result()
                if result:
                    merged_updates.update(result)
                    print(f"  ✅ [{agent_name}] Collected")
            except Exception as e:
                error_msg = f"[{agent_name}] Failed: {str(e)}"
                print(f"  ❌ {error_msg}")
                errors.append(error_msg)

    merged_updates["errors"] = errors
    return merged_updates


def _run_with_timeout(fn, state: DDState, timeout: int) -> dict:
    start = time.time()
    try:
        result = fn(state)
        elapsed = round(time.time() - start, 1)
        print(f"       ⏱  Took {elapsed}s")
        return result
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        raise RuntimeError(f"Agent failed after {elapsed}s: {e}") from e


# Build the Graph

def build_graph() -> StateGraph:
    """
    Constructs and compiles the LangGraph StateGraph.
    Phase 3: adds doc_ingest_node and rag_node.
    """
    builder = StateGraph(DDState)

    # Register all nodes
    builder.add_node("seed_node",        run_seed_crawler)
    builder.add_node("doc_ingest_node",  run_doc_ingest)
    builder.add_node("specialists_node", run_specialists_parallel)
    builder.add_node("validator_node",   run_validator)
    builder.add_node("risk_node",        run_risk_scorer)
    builder.add_node("rag_node",         run_rag_agent)
    builder.add_node("synthesis_node",   run_synthesis)

    # Wire edges — sequential flow
    builder.add_edge(START,               "seed_node")
    builder.add_edge("seed_node",         "doc_ingest_node")
    builder.add_edge("doc_ingest_node",   "specialists_node")
    builder.add_edge("specialists_node",  "validator_node")
    builder.add_edge("validator_node",    "risk_node")
    builder.add_edge("risk_node",         "rag_node")
    builder.add_edge("rag_node",          "synthesis_node")
    builder.add_edge("synthesis_node",    END)

    return builder.compile()


dd_graph = build_graph()