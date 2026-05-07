"""
qa/qa_graph.py — ReAct Q&A agent using prompt-based JSON dispatch.

WHY this approach instead of bind_tools / create_react_agent:
  - Groq's llama-3.3-70b generates tool calls in native <function=...> format
    which is incompatible with LangChain's OpenAI-style tool calling
  - bind_tools causes 400 errors on Groq for this reason
  - create_react_agent is deprecated in LangGraph v1.0
  - Prompt-based dispatch works with ANY LLM, zero compatibility issues

HOW the ReAct loop works:
  Step 1 — Send question + system prompt to LLM
  Step 2 — LLM responds with JSON: {"action": "tool_name", "input": "query"}
  Step 3 — We call the tool, append the result to context
  Step 4 — Repeat until LLM responds with {"action": "final_answer", "answer": "..."}
  Step 5 — Return the final answer + tool usage log
"""

import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from tools.llm_factory import get_llm, call_llm_with_retry
from qa.qa_tools import build_tools


# ── ReAct system prompt ───────────────────────────────────────────────────────

REACT_SYSTEM_PROMPT = """You are an expert due diligence analyst assistant.

CONTEXT:
{context}

You have access to 4 tools. To use a tool or give a final answer,
you MUST respond with ONLY a valid JSON object — no other text whatsoever.

AVAILABLE TOOLS:

1. search_report
   Use for: anything in the DD report, team, funding, financials, tech, competitors
   Format:  {{"action": "search_report", "input": "your search query"}}

2. search_web
   Use for: info NOT in the report, latest news, current data
   Format:  {{"action": "search_web", "input": "your web search query"}}

3. get_risk_detail
   Use for: specific risk score questions
   Input must be one of: founder_risk | market_risk | financial_risk | technical_risk | reputational_risk | overall | all
   Format:  {{"action": "get_risk_detail", "input": "financial_risk"}}

4. compare_history
   Use for: "has X changed?", "compare with last time" questions
   Input must be one of: risk_scores | funding | team | financials | competitors | overall
   Format:  {{"action": "compare_history", "input": "risk_scores"}}

FINAL ANSWER:
When you have enough information to answer, respond with:
{{"action": "final_answer", "answer": "your complete answer here"}}

STRICT RULES:
- ALWAYS try search_report first before search_web
- Output ONLY valid JSON — absolutely no markdown, no explanation, no preamble
- Keep final answers under 350 words and cite specific numbers
- Never make up data — only use what tools return
"""


def _build_context_block(run_context: dict) -> str:
    """Short company context injected into the system prompt."""
    company_name = run_context.get("company_name", "the company")
    sector_label = run_context.get("sector_label", "Technology")
    risk_score   = run_context.get("overall_risk_score", "N/A")
    confidence   = run_context.get("dd_confidence_score", "N/A")
    has_docs     = run_context.get("has_documents", False)
    doc_note     = "Uploaded docs searchable via search_report." if has_docs else "No docs uploaded."
    return (
        f"Company: {company_name} | Sector: {sector_label} | "
        f"Risk: {risk_score}/10 | Confidence: {confidence}/100 | {doc_note}"
    )


def _parse_action(text: str) -> dict:
    """
    Parse LLM JSON response into an action dict.
    Handles: clean JSON, JSON in code fences, JSON embedded in text.
    Falls back to treating the whole response as a final answer.
    """
    text = text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        inner_lines = lines[1:]
        if inner_lines and inner_lines[-1].strip() == "```":
            inner_lines = inner_lines[:-1]
        text = "\n".join(inner_lines).strip()

    # Attempt 1: direct JSON parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "action" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    # Attempt 2: find JSON object anywhere in the text
    match = re.search(r'\{[^{}]*"action"\s*:[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict) and "action" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

    # Fallback: treat entire response as a final answer
    return {"action": "final_answer", "answer": text}


# ── Public: build agent ───────────────────────────────────────────────────────

def build_qa_agent(run_context: dict) -> dict:
    """
    Build the Q&A agent as a simple component dict.

    Returns a dict with: llm, tools (callable dict), system prompt.
    This avoids all LangGraph / bind_tools compatibility issues.

    Usage:
        agent = build_qa_agent(run_context)
        result = ask_question(agent, "Who are the founders?")
    """
    tool_objects = build_tools(run_context)

    # Convert LangChain @tool objects to a {name: tool} callable dict
    tools_callable = {tool.name: tool for tool in tool_objects}

    llm    = get_llm(temperature=0.1)
    system = REACT_SYSTEM_PROMPT.format(
        context=_build_context_block(run_context)
    )

    return {
        "llm":    llm,
        "tools":  tools_callable,
        "system": system,
    }


# ── Public: ask a question ────────────────────────────────────────────────────

def ask_question(
    agent:          dict,
    question:       str,
    chat_history:   list[dict] | None = None,
    max_iterations: int = 5,
) -> dict:
    """
    Run the prompt-based ReAct loop for a single question.

    Args:
        agent:          Dict from build_qa_agent()
        question:       The user's question
        chat_history:   List of {"role": "user"/"assistant", "content": str}
        max_iterations: Max tool calls before forcing a final answer

    Returns:
        {answer, tools_used, tool_calls, error}
    """
    llm    = agent["llm"]
    tools  = agent["tools"]
    system = agent["system"]

    # Build conversation context from history
    history_lines = []
    for msg in (chat_history or [])[-4:]:  # last 2 exchanges max
        role    = msg.get("role", "user").upper()
        content = msg.get("content", "")[:400]
        history_lines.append(f"{role}: {content}")

    if history_lines:
        base_question = (
            "PREVIOUS CONVERSATION:\n"
            + "\n".join(history_lines)
            + f"\n\nCURRENT QUESTION: {question}"
        )
    else:
        base_question = f"QUESTION: {question}"

    tools_used:     list[str]  = []
    tool_calls_log: list[dict] = []
    observations:   list[dict] = []  # accumulates tool results across steps

    for step in range(max_iterations):

        # ── Build this step's user message ────────────────────────────────
        if observations:
            obs_text = "\n\n".join([
                f"[Tool: {o['tool']}]\n{o['result'][:800]}"
                for o in observations
            ])
            step_content = (
                f"{base_question}\n\n"
                f"TOOL RESULTS SO FAR:\n{obs_text}\n\n"
                f"Now decide: call another tool OR give a final_answer."
            )
        else:
            step_content = base_question

        messages = [
            SystemMessage(content=system),
            HumanMessage(content=step_content),
        ]

        # ── Call LLM ──────────────────────────────────────────────────────
        try:
            response = call_llm_with_retry(
                llm, messages, agent_name=f"QA-Step{step+1}"
            )
            raw_text = response.content
        except Exception as e:
            return {
                "answer":     f"Rate limit or API error: {str(e)[:200]}",
                "tools_used": tools_used,
                "tool_calls": tool_calls_log,
                "error":      str(e),
            }

        # ── Parse the action ───────────────────────────────────────────────
        action      = _parse_action(raw_text)
        action_type = action.get("action", "final_answer")

        # ── Final answer ───────────────────────────────────────────────────
        if action_type == "final_answer":
            return {
                "answer":     action.get("answer", raw_text),
                "tools_used": tools_used,
                "tool_calls": tool_calls_log,
                "error":      None,
            }

        # ── Known tool call ────────────────────────────────────────────────
        if action_type in tools:
            tool_input = action.get("input", "")
            print(f"  🔧 [QA] Tool: {action_type}({tool_input[:60]})")

            try:
                # LangChain @tool objects are invoked with .invoke()
                result     = tools[action_type].invoke(tool_input)
                result_str = str(result)
            except Exception as e:
                result_str = f"Tool error: {str(e)[:200]}"

            # Record usage
            if action_type not in tools_used:
                tools_used.append(action_type)

            preview = result_str[:300] + "..." if len(result_str) > 300 else result_str
            tool_calls_log.append({"tool": action_type, "output": preview})

            # Store full result for next reasoning step
            observations.append({"tool": action_type, "result": result_str})
            continue

        # ── Unknown action — treat as final answer ─────────────────────────
        return {
            "answer":     raw_text,
            "tools_used": tools_used,
            "tool_calls": tool_calls_log,
            "error":      None,
        }

    # ── Max iterations reached — summarize what we found ──────────────────
    if observations:
        obs_text = "\n\n".join([
            f"[Tool: {o['tool']}]\n{o['result'][:600]}"
            for o in observations
        ])
        try:
            summary_msgs = [
                SystemMessage(content=system),
                HumanMessage(content=(
                    f"QUESTION: {question}\n\n"
                    f"TOOL RESULTS:\n{obs_text}\n\n"
                    f'Using ONLY the results above, respond with:\n'
                    f'{{"action": "final_answer", "answer": "your answer"}}'
                )),
            ]
            r = call_llm_with_retry(llm, summary_msgs, "QA-Summary")
            final = _parse_action(r.content)
            return {
                "answer":     final.get("answer", r.content),
                "tools_used": tools_used,
                "tool_calls": tool_calls_log,
                "error":      None,
            }
        except Exception:
            pass

    return {
        "answer":     "Reached max steps without a complete answer. Try a more specific question.",
        "tools_used": tools_used,
        "tool_calls": tool_calls_log,
        "error":      "max_iterations",
    }


# ── Context builders (unchanged) ──────────────────────────────────────────────

def build_run_context(final_state: dict) -> dict:
    """Build run_context from a DDState final_state dict."""
    seed_data    = final_state.get("seed_data", {})
    company_name = seed_data.get("company_name", "Unknown Company")
    company_url  = final_state.get("company_url", "")
    company_slug = (
        company_url
        .replace("https://", "").replace("http://", "")
        .replace("www.", "").split("/")[0].split(".")[0].lower()
    )
    try:
        from prompts.sectors import detect_sector, get_sector_label
        sector_label = get_sector_label(detect_sector(seed_data))
    except Exception:
        sector_label = "Technology"

    risk_scorecard = final_state.get("risk_scorecard", {})
    uploaded_files = final_state.get("uploaded_files", [])

    return {
        "run_id":              final_state.get("run_id", ""),
        "company_name":        company_name,
        "company_url":         company_url,
        "company_slug":        company_slug,
        "sector_label":        sector_label,
        "report_markdown":     final_state.get("report_markdown", ""),
        "risk_scorecard":      risk_scorecard,
        "investor_data":       final_state.get("investor_data", {}),
        "team_data":           final_state.get("team_data", {}),
        "financials_data":     final_state.get("financials_data", {}),
        "competitor_data":     final_state.get("competitor_data", {}),
        "has_documents":       len(uploaded_files) > 0,
        "overall_risk_score":  risk_scorecard.get("overall_risk_score", "N/A"),
        "dd_confidence_score": risk_scorecard.get("dd_confidence_score", "N/A"),
    }


def build_run_context_from_db(run) -> dict:
    """Build run_context from a ResearchRun DB object."""
    try:
        from prompts.sectors import detect_sector, get_sector_label
        sector_label = get_sector_label(detect_sector(run.seed_data))
    except Exception:
        sector_label = "Technology"

    return {
        "run_id":              run.run_id,
        "company_name":        run.company_name,
        "company_url":         run.company_url,
        "company_slug":        run.company_slug,
        "sector_label":        sector_label,
        "report_markdown":     run.report_markdown,
        "risk_scorecard":      run.risk_scorecard,
        "investor_data":       run.investor_data,
        "team_data":           run.team_data,
        "financials_data":     run.financials_data,
        "competitor_data":     run.competitor_data,
        "has_documents":       run.has_documents,
        "overall_risk_score":  run.overall_risk_score,
        "dd_confidence_score": run.dd_confidence_score,
    }


if __name__ == "__main__":
    print("Q&A Agent test — loading latest run from DB...\n")
    try:
        from persistence.db import init_db
        from persistence.queries import list_runs
        init_db()
        runs = list_runs(limit=1)
        if not runs:
            print("❌ No runs in DB. Run the pipeline first.")
        else:
            run   = runs[0]
            print(f"✅ Testing with: {run.company_name} ({run.run_id})\n")
            ctx   = build_run_context_from_db(run)
            agent = build_qa_agent(ctx)

            questions = [
                "Who are the founders?",
                "What is the financial risk score and why?",
                "What are the top 3 competitors?",
            ]
            for q in questions:
                print(f"📩 Q: {q}")
                result = ask_question(agent, q)
                print(f"🔧 Tools: {result['tools_used']}")
                print(f"💬 A: {result['answer'][:300]}...")
                if result["error"]:
                    print(f"❌ Error: {result['error']}")
                print()
    except Exception as e:
        import traceback
        print(f"❌ Test failed: {e}")
        traceback.print_exc()