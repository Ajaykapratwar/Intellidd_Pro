"""
qa/qa_tools.py — Tool definitions for the ReAct Q&A agent.

4 tools available to the agent:
  1. search_report      — semantic search over ChromaDB (report + uploaded docs)
  2. search_web         — DuckDuckGo search for info not in the report
  3. get_risk_detail    — retrieve specific risk dimension breakdown
  4. compare_history    — compare current run against a past run from SQLite

Each tool's docstring IS the agent's instruction for when to use it.
Keep docstrings precise — the LLM reads them at every reasoning step.

Usage (internal — called by qa_graph.py):
    from qa.qa_tools import build_tools
    tools = build_tools(run_context)
"""

import json
from typing import Optional

from langchain_core.tools import tool

def build_tools(run_context: dict) -> list:
    """
    Build all Q&A tools bound to a specific run's context.

    Args:
        run_context: Dict containing:
            run_id           — current run ID (for ChromaDB collection)
            company_name     — for display in tool outputs
            report_markdown  — full report text for keyword search fallback
            risk_scorecard   — dict from risk_scorer
            has_documents    — bool: were docs uploaded?
            company_slug     — for SQLite history lookup

    Returns:
        List of LangChain tool objects ready for the ReAct agent.
    """

    run_id = run_context.get("run_id", "")
    company_name = run_context.get("company_name", "the company")
    report_markdown = run_context.get("report_markdown", "")
    risk_scorecard = run_context.get("risk_scorecard", {})
    has_documents = run_context.get("has_documents", False)
    company_slug = run_context.get("company_slug", "")

    #  ── Tool 1: Search Report ─────────────────────────────────────────────────

    @tool
    def search_report(query: str) -> str:
        """
        Search the due diligence report and any uploaded documents
        for information relevant to the query.

        Use this tool FIRST for any question about:
        - The company's team, funding, financials, tech stack, press, or social media
        - Risk scores or competitive positioning
        - Anything that was researched during the due diligence pipeline
        - Content from uploaded pitch decks or financial documents

        Args:
            query: A natural language question or keyword phrase to search for.
                   Example: "What is the revenue estimate?"
                            "Who are the founders?"
                            "What is the biggest risk?"

        Returns:
            Relevant excerpts from the report and uploaded documents.
        """

        results = []

        # Strategy 1: ChromaDB semantic search (if documents were uploaded)
        if has_documents and run_id:
            try:
                from rag.vector_store import VectorStore
                vs = VectorStore(run_id=run_id)
                if vs.is_populated:
                    doc_results = vs.query(query, n_results=4)
                    if doc_results:
                        results.append("=== From Uploaded Documents ===")
                        for r in doc_results:
                            results.append(f"[{r['source_file']} | {r['page_or_sheet']}]\n{r['text']}")
            except Exception as e:
                results.append(f["Document search is unavailable: {e}"])
        
        # Strategy 2: Keyword search through report markdown
        if report_markdown:
            query_lower = query.lower()
            query_words = [w for w in query_lower.split() if len(w) > 3]

            # Strategy 2: Keyword search through report markdow
            paragraphs = [p.strip() for p in report_markdown.split("\n\n") if len(p.strip()) > 50]
            scored = []
            for para in paragraphs:
                para_lower = para.lower()
                score = sum(1 for word in query_words if word in para_lower)
                if score > 0:
                    scored.append((score, para))

            scored.sort(key=lambda x: x[0], reverse=True)
            top_paragraphs = [p for _, p in scored[:5]]

            if top_paragraphs:
                results.append("\n=== FROM DUE DILIGENCE REPORT ===")
                results.extend(top_paragraphs)
            
        if not results:
            return (
                f"No specific information found for '{query}' in the report "
                f"or uploaded documents. Consider using search_web to find "
                f"additional information."
            )
        return "\n\n".join(results)[:4000]

    #  ── Tool 2: Search Web ────────────────────────────────────────────────────
    @tool
    def search_web(query: str) -> str:
        """
        Search the web using DuckDuckGo for current information
        that is NOT available in the due diligence report.

        Use this tool ONLY when:
        - The user asks about something not covered in the report
        - The user asks for the very latest news or developments
        - search_report returned no useful results
        - The user explicitly asks you to search the web

        Do NOT use this tool for information that is already in the report.
        Always try search_report first.

        Args:
            query: A specific web search query.
                   Include the company name for best results.
                   Example: "Stripe latest funding round 2025"
                            "Stripe competitors payment processing"

        Returns:
            Web search results with titles, URLs, and snippets.
        """

        try:
            from tools.search import search_web as ddg_search
            results = ddg_search(query, max_results=5)

            if not results:
                return f"No web results found for '{query}'"
            
            formatted = [f"Web search results for '{query}'\n"]
            for i, r in enumerate(results, 1):
                formatted.append(
                    f"[Result {i}]\n"
                    f"Title: {r.title}\n"
                    f"URL: {r.url}\n"
                    f"Snippet: {r.snippet}\n"
                )
            return "\n".join(formatted)