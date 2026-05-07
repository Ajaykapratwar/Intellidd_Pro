"""
ui/components/trace_card.py — Pipeline performance + LangSmith trace card.

Renders:
  - Per-agent timing horizontal bars (identifies bottlenecks visually)
  - Total duration, token estimate, parallel efficiency %
  - "View in LangSmith" button (if trace URL is available)
  - Setup guidance if LangSmith is not configured

Usage:
    from ui.components.trace_card import render_trace_card
    render_trace_card(performance_stats)
"""

import streamlit as st
from tools.observability import format_duration, check_langsmith_config


# Agent display config: human-readable names + colors per agent
AGENT_DISPLAY = {
    "seed":        ("🌱 Seed Crawler",      "#1d63db"),
    "team":        ("👥 Team Agent",        "#7c3aed"),
    "investors":   ("💰 Investor Agent",    "#0e7490"),
    "press":       ("📰 Press Agent",       "#b45309"),
    "financials":  ("📊 Financials Agent",  "#15803d"),
    "tech_stack":  ("⚙️  Tech Stack Agent", "#be185d"),
    "social":      ("📱 Social Agent",      "#1d4ed8"),
    "competitors": ("🏆 Competitor Agent",  "#c2410c"),
    "validator":   ("🔍 Validator",         "#4338ca"),
    "risk":        ("📈 Risk Scorer",       "#0f766e"),
    "rag":         ("🗄️  Document RAG",     "#92400e"),
    "synthesis":   ("📝 Synthesis",         "#166534"),
}


def _timing_bar_html(agent_key: str, seconds: float, max_seconds: float) -> str:
    """
    Render a single horizontal timing bar as HTML.

    Bar width is proportional to agent's time vs the slowest agent.
    Color matches the agent's theme color.
    """
    label, color = AGENT_DISPLAY.get(agent_key, (agent_key.title(), "#64748b"))
    pct = min(100, round((seconds / max_seconds * 100) if max_seconds > 0 else 0))

    return f"""
    <div style="margin-bottom: 6px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:2px;">
            <span style="font-size:0.78rem; color:#cbd5e1;">{label}</span>
            <span style="font-size:0.78rem; color:#94a3b8; font-family:monospace;">
                {format_duration(seconds)}
            </span>
        </div>
        <div style="background:#1e293b; border-radius:4px; height:8px; overflow:hidden;">
            <div style="
                width:{pct}%;
                height:100%;
                background:{color};
                border-radius:4px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """


def render_trace_card(performance_stats: dict) -> None:
    """
    Render the full pipeline performance + LangSmith trace card.

    Args:
        performance_stats: Dict from tools.observability.build_performance_summary()
                           If empty dict, renders a placeholder.
    """
    if not performance_stats:
        st.info(
            "⚡ Performance data not available. "
            "Run a pipeline to see agent timing and LangSmith traces."
        )
        return

    agent_timings   = performance_stats.get("agent_timings", {})
    total_duration  = performance_stats.get("total_duration", 0)
    slowest_agent   = performance_stats.get("slowest_agent", "unknown")
    total_tokens    = performance_stats.get("total_tokens_est", 0)
    model_used      = performance_stats.get("model_used", "unknown")
    trace_url       = performance_stats.get("trace_url", "")
    time_saved      = performance_stats.get("parallel_time_saved_seconds", 0)
    efficiency_pct  = performance_stats.get("parallel_efficiency_pct", 0)
    docs_uploaded   = performance_stats.get("docs_uploaded", 0)
    agent_count     = performance_stats.get("agent_count", 0)

    ls_config = check_langsmith_config()

    # ── Header metrics row ────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric(
            "⏱ Total Time",
            format_duration(total_duration),
            help="Wall-clock time from pipeline start to report saved",
        )
    with m2:
        st.metric(
            "🤖 Agents Run",
            f"{agent_count}",
            help="Number of LLM agents that executed",
        )
    with m3:
        st.metric(
            "🧠 Tokens (est.)",
            f"~{total_tokens:,}",
            help="Estimated total tokens across all agent LLM calls",
        )
    with m4:
        slowest_display = AGENT_DISPLAY.get(slowest_agent, (slowest_agent.title(), ""))[0]
        st.metric(
            "🐢 Slowest Agent",
            slowest_display[:20],
            help="Agent that took the longest to complete",
        )
    with m5:
        st.metric(
            "⚡ Time Saved",
            f"{format_duration(time_saved)}",
            delta=f"{efficiency_pct}% parallel efficiency",
            delta_color="normal",
            help="Time saved by running specialist agents in parallel vs sequential",
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # ── Per-agent timing bars + LangSmith panel ───────────────────────────────
    bars_col, langsmith_col = st.columns([3, 2])

    # Left: timing bars
    with bars_col:
        st.markdown(
            "<div style='font-weight:700;color:#e2e8f0;margin-bottom:0.8rem'>"
            "📊 Per-Agent Timing"
            "</div>",
            unsafe_allow_html=True,
        )

        if not agent_timings:
            st.caption("No timing data available.")
        else:
            # Find max for proportional bars
            max_time = max(agent_timings.values()) if agent_timings else 1

            # Render sequential agents first (seed, validator, risk, rag, synthesis)
            sequential_keys = ["seed", "validator", "risk", "rag", "synthesis"]
            parallel_keys   = ["team", "investors", "press", "financials",
                                "tech_stack", "social", "competitors"]

            # Sequential agents
            seq_bars = ""
            for key in sequential_keys:
                if key in agent_timings:
                    seq_bars += _timing_bar_html(key, agent_timings[key], max_time)

            if seq_bars:
                st.markdown(
                    "<div style='font-size:0.72rem;color:#64748b;"
                    "margin-bottom:4px;margin-top:4px'>SEQUENTIAL</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(seq_bars, unsafe_allow_html=True)

            # Parallel agents
            par_bars = ""
            for key in parallel_keys:
                if key in agent_timings:
                    par_bars += _timing_bar_html(key, agent_timings[key], max_time)

            if par_bars:
                st.markdown(
                    "<div style='font-size:0.72rem;color:#64748b;"
                    "margin-bottom:4px;margin-top:8px'>PARALLEL (ran simultaneously)</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(par_bars, unsafe_allow_html=True)

    # Right: LangSmith panel
    with langsmith_col:
        st.markdown(
            "<div style='font-weight:700;color:#e2e8f0;margin-bottom:0.8rem'>"
            "🔭 LangSmith Observability"
            "</div>",
            unsafe_allow_html=True,
        )

        if ls_config["enabled"] and trace_url:
            # Full trace URL available
            st.markdown(
                f"""
                <div style="background:#1e293b;border:1px solid #1d63db;
                border-radius:10px;padding:1rem;">
                    <div style="color:#22c55e;font-weight:700;margin-bottom:0.5rem">
                        ✅ Trace captured
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem;margin-bottom:0.8rem">
                        Project: <code style="color:#60a5fa">{ls_config['project']}</code>
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem;margin-bottom:0.8rem">
                        Model: <code style="color:#60a5fa">{model_used}</code>
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem">
                        Every agent call, tool invocation, and LLM prompt/response
                        is inspectable in the dashboard.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br/>", unsafe_allow_html=True)
            st.link_button(
                "🔗 View Full Trace in LangSmith",
                trace_url,
                use_container_width=True,
                type="primary",
            )

        elif ls_config["enabled"] and not trace_url:
            # Tracing on but URL not captured
            st.markdown(
                f"""
                <div style="background:#1e293b;border:1px solid #f59e0b;
                border-radius:10px;padding:1rem;">
                    <div style="color:#f59e0b;font-weight:700;margin-bottom:0.5rem">
                        ⚠️ Trace indexing
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem;margin-bottom:0.5rem">
                        Project: <code>{ls_config['project']}</code>
                    </div>
                    <div style="color:#94a3b8;font-size:0.8rem">
                        Tracing is enabled. The run may still be indexing.
                        Check your LangSmith dashboard directly.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button(
                "🔗 Open LangSmith Dashboard",
                f"https://smith.langchain.com",
                use_container_width=True,
            )

        else:
            # LangSmith not configured — show setup guide
            st.markdown(
                """
                <div style="background:#1e293b;border:1px solid #334155;
                border-radius:10px;padding:1rem;">
                    <div style="color:#94a3b8;font-weight:700;margin-bottom:0.5rem">
                        ℹ️ LangSmith not configured
                    </div>
                    <div style="color:#64748b;font-size:0.8rem;margin-bottom:0.8rem">
                        Enable full agent observability in 3 steps:
                    </div>
                    <div style="font-size:0.78rem;color:#94a3b8;">
                        1. Sign up free at smith.langchain.com<br/>
                        2. Add to .env:<br/>
                        <code style="color:#60a5fa">LANGCHAIN_API_KEY=your_key</code><br/>
                        <code style="color:#60a5fa">LANGCHAIN_TRACING_V2=true</code><br/>
                        3. Restart the app
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.link_button(
                "→ Get Free LangSmith Key",
                "https://smith.langchain.com",
                use_container_width=True,
            )

        # Model info box
        if docs_uploaded > 0:
            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:#1e293b;border-radius:8px;padding:0.6rem;"
                f"font-size:0.8rem;color:#a78bfa;border:1px solid #4c1d95'>"
                f"📄 {docs_uploaded} document(s) processed via ChromaDB RAG"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Parallel savings callout ──────────────────────────────────────────────
    if time_saved > 10:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:rgba(34,197,94,0.1);border:1px solid #22c55e;"
            f"border-radius:8px;padding:0.7rem 1rem;font-size:0.85rem;color:#86efac'>"
            f"⚡ <strong>Parallel execution saved {format_duration(time_saved)}</strong> "
            f"— running 7 agents simultaneously instead of sequentially "
            f"({efficiency_pct}% more efficient)"
            f"</div>",
            unsafe_allow_html=True,
        )