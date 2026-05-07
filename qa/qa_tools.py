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
                results.append(f"[Document search is unavailable: {e}]")
        
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
        
        except Exception as e:
            return f"Web search failed: {str(e)}"
    
    # ── Tool 3: Get Risk Detail ───────────────────────────────────────────────
    @tool
    def get_risk_detail(dimension: str) -> str:
        """
        Get the detailed breakdown for a specific risk dimension
        from the quantitative risk scorecard.

        Use this tool when the user asks about:
        - A specific risk score ("what is the financial risk score?")
        - Risk factors or evidence for a dimension
        - How to mitigate a specific risk
        - The overall DD confidence score

        Args:
            dimension: The risk dimension to retrieve. Must be one of:
                       "founder_risk"      — team and leadership risk
                       "market_risk"       — competitive and market risk
                       "financial_risk"    — financial health risk
                       "technical_risk"    — technology and engineering risk
                       "reputational_risk" — press, brand, and PR risk
                       "overall"           — overall risk score and summary
                       "all"               — complete scorecard

        Returns:
            Detailed risk breakdown including score, severity,
            key factors, evidence, and mitigation strategy.
        """
        if not risk_scorecard:
            return "No risk scorecard available for this run."
        
        dimension = dimension.lower().strip()

        if dimension == "overall":
            return json.dumps({
                "overall_risk_score": risk_scorecard.get("overall_risk_score"),
                "dd_confidence_score": risk_scorecard.get("dd_confidence_score"),
                "highest_priority_risk": risk_scorecard.get("highest_priority_risk"),
                "risk_summary": risk_scorecard.get("risk_summary")
            }, indent=2)
        
        if dimension == "all":
            return json.dumps(risk_scorecard, indent=2)[:3000]
        
        valid_dimensions = [
            "founder_risk",
            "market_risk",
            "financial_risk",
            "technical_risk",
            "reputational_risk"
        ]

        # Fuzzy match — handle user typing "financial" instead of "financial_risk"
        matched = None
        for valid in valid_dimensions:
            if dimension in valid or valid.split("_")[0] in dimension:
                matched = valid
                break

            if not matched:
                return (
                    f"Unknown dimension: '{dimension}'."
                    f"Valid options: {', '.join(valid_dimensions)}, overall, all"
                )
            
            dim_data = risk_scorecard.get(matched, {})
            if not dim_data:
                return f"No data available for dimension: {matched}"
            
            return json.dumps({
                "dimension": matched,
                "score": dim_data.get("score"),
                "severity": dim_data.get("severity"),
                "key_factors": dim_data.get("key_factors", []),
                "evidence": dim_data.get("evidence"),
                "mitigation": dim_data.get("mitigation")
            }, indent=2)
        
    # ── Tool 4: Compare History ───────────────────────────────────────────────
    @tool
    def compare_history(field: str) -> str:
        """
        Compare the current run's data against past research runs
        for the same company stored in the database.

        Use this tool when the user asks:
        - "Has anything changed since last time?"
        - "How does this compare to the previous report?"
        - "Has the risk score improved?"
        - "What was the funding last time we researched this?"
        - Any question involving historical comparison or trends

        Args:
            field: What to compare. Examples:
                   "risk_scores"    — compare all 5 risk dimensions
                   "funding"        — compare funding/investor data
                   "team"           — compare team size and founders
                   "financials"     — compare revenue and financial signals
                   "competitors"    — compare competitive positioning
                   "overall"        — compare all key metrics

        Returns:
            A side-by-side comparison of current vs. past run data,
            or a message if no past runs exist for this company.
        """
        if not company_slug:
            return "No company slug available for history lookup."

        try:
            from persistence.queries import get_runs_for_company
            past_runs = get_runs_for_company(company_slug)

            # filter out current run
            past_runs = [r for r in past_runs if r.run_id != run_id]

            if not past_runs:
                return (
                    f"No previous research runs found for {company_name}. "
                    f"This appears to be the first time we've researched this company."
                )

            # Sort by date (newest first)
            past_runs.sort(key=lambda x: x.created_at, reverse=True)
            latest_past = past_runs[0]

            field = field.lower().strip()

            if field in ("risk_scores", "risk", "overall"):
                current_risk = risk_scorecard
                past_risk = latest_past.risk_scorecard

                dims = [
                    "founder_risk",
                    "market_risk",
                    "financial_risk",
                    "technical_risk",
                    "reputational_risk"
                ]
                comparison = {
                    "comparison_date": latest_past.created_at_display,
                    "dimension": {}
                }
                for dim in dims:
                    curr_score = current_risk.get(dim, {}).get("score", "N/A")
                    past_score = past_risk.get(dim, {}).get("score", "N/A")

                    try:
                        delta = int(curr_score) - int(past_score)
                        direction = "↑ increased" if delta > 0 else "↓ decreased" if delta < 0 else "→ unchanged"
                    except Exception as e:
                        delta = None
                        direction = "N/A"
                    comparison["dimesnions"][dim] = {
                        "current": curr_score,
                        "past": past_score,
                        "delta": delta,
                        "direction": direction
                    }
                comparison["overall_risk"] = {
                    "current": risk_scorecard.get("overall_risk_score", "N/A"),
                    "previous": latest_past.overall_risk_score,
                }
                comparison["dd_confidence"] = {
                    "current": risk_scorecard.get("dd_confidence_score", "N/A"),
                    "previous": latest_past.dd_confidence_score,
                }
                return json.dumps(comparison, indent=2)
            
            elif field in ("funding", "investors"):
                return json.dumps({
                    "comparison_date": latest_past.created_at_display,
                    "current": {
                        "total_funding": run_context.get("investor_data", {}).get("total_funding_usd", "Unknown"),
                        "last_round_type": run_context.get("investor_data", {}).get("last_round_type", "Unknown"),
                        "last_round_date": run_context.get("investor_data", {}).get("last_round_date", "Unknown"),
                    },
                    "previous": {
                        "total_funding": latest_past.investor_data.get("total_funding_usd", "Unknown"),
                        "last_round_type": latest_past.investor_data.get("last_round_type", "Unknown"),
                        "last_round_date": latest_past.investor_data.get("last_round_date", "Unknown"),
                    },
                }, indent=2)
            
            elif field in ("team", "founders"):
                curr_founders = run_context.get("team_data", {}).get("founders", [])
                past_founders = latest_past.team_data.get("founders", [])
                return json.dumps({
                    "comparison_date": latest_past.created_at_display,
                    "current_founder_count": len(curr_founders),
                    "previous_founders_count": len(past_founders),
                    "current_team_size": run_context.get("team_data", {}).get("team_size_estimate", "Unknown"),
                    "previous_team_size": latest_past.team_data.get("team_size_estimate", "Unknown"),
                    "current_founders": [f.get("name") for f in curr_founders],
                    "previous_founders": [f.get("name") for f in past_founders],
                }, indent=2)

            elif field in ("financials", "revenue", "financial"):
                return json.dumps({
                    "comparison_date": latest_past.created_at_display,
                    "current": {
                        "revenue_estimate":     run_context.get("financials_data", {}).get("revenue_estimate", "Unknown"),
                        "revenue_growth":       run_context.get("financials_data", {}).get("revenue_growth_signal", "Unknown"),
                        "profitability_signal": run_context.get("financials_data", {}).get("profitability_signal", "Unknown"),
                    },
                    "previous": {
                        "revenue_estimate":     latest_past.financials_data.get("revenue_estimate", "Unknown"),
                        "revenue_growth":       latest_past.financials_data.get("revenue_growth_signal", "Unknown"),
                        "profitability_signal": latest_past.financials_data.get("profitability_signal", "Unknown"),
                    },
                }, indent=2)

            elif field in ("competitors", "competition"):
                return json.dumps({
                    "comparison_date": latest_past.created_at_display,
                    "current": {
                        "market_position":      run_context.get("competitor_data", {}).get("market_position", "Unknown"),
                        "differentiation_score": run_context.get("competitor_data", {}).get("differentiation_score", "N/A"),
                        "competitor_count":     len(run_context.get("competitor_data", {}).get("competitors", [])),
                    },
                    "previous": {
                        "market_position":      latest_past.competitor_data.get("market_position", "Unknown"),
                        "differentiation_score": latest_past.competitor_data.get("differentiation_score", "N/A"),
                        "competitor_count":     len(latest_past.competitor_data.get("competitors", [])),
                    },
                }, indent=2)

            else:
                # General comparison — key metrics only
                return json.dumps({
                    "message": f"Showing general comparison with run from {latest_past.created_at_display}",
                    "current": {
                        "overall_risk":    risk_scorecard.get("overall_risk_score", "N/A"),
                        "dd_confidence":   risk_scorecard.get("dd_confidence_score", "N/A"),
                        "market_position": run_context.get("competitor_data", {}).get("market_position", "Unknown"),
                        "total_funding":   run_context.get("investor_data", {}).get("total_funding_usd", "Unknown"),
                    },
                    "previous": {
                        "overall_risk":    latest_past.overall_risk_score,
                        "dd_confidence":   latest_past.dd_confidence_score,
                        "market_position": latest_past.competitor_data.get("market_position", "Unknown"),
                        "total_funding":   latest_past.investor_data.get("total_funding_usd", "Unknown"),
                    },
                }, indent=2)

        except Exception as e:
            return f"History comparison failed: {str(e)}"

    return [search_report, search_web, get_risk_detail, compare_history]