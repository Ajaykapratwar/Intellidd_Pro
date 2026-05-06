"""
ui/components/report_card.py — Past run display component for History page.

Usage:
    from ui.components.report_card import render_run_card, render_run_summary_row
    render_run_card(run)          # full expanded view
    render_run_summary_row(run)   # compact table row
"""

import json
import streamlit as st

from persistence.models import ResearchRun
from persistence import queries


def render_run_summary_row(run: ResearchRun) -> None:
    """
    Renders a single compact row for a run in the history list.
    Shows key metrics and action buttons inline.
    """
    col1, col2, col3, col4, col5, col6, col7 = st.columns(
        [2.5, 1.2, 1.0, 1.0, 1.0, 1.0, 1.5]
    )

    with col1:
        star = "⭐" if run.is_starred else "☆"
        status_icon = "✅" if run.is_complete else "⚠️"
        doc_badge = " 📄" if run.has_documents else ""
        st.markdown(
            f"**{status_icon} {run.company_name}**{doc_badge}  \n"
            f"<span style='color:#64748b;font-size:0.8rem'>"
            f"{run.created_at_display}</span>",
            unsafe_allow_html=True,
        )

    with col2:
        sector_short = run.sector_detected.split("/")[0].strip()[:18]
        st.markdown(
            f"<span style='background:#1e293b;padding:2px 8px;"
            f"border-radius:10px;font-size:0.75rem;color:#93c5fd'>"
            f"{sector_short}</span>",
            unsafe_allow_html=True,
        )

    with col3:
        risk = run.overall_risk_score
        if risk is not None:
            color = "#22c55e" if risk <= 3 else "#f59e0b" if risk <= 6 else "#ef4444"
            st.markdown(
                f"<span style='color:{color};font-weight:700'>{risk}/10</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<span style='color:#64748b'>N/A</span>", unsafe_allow_html=True)

    with col4:
        conf = run.dd_confidence_score
        st.markdown(
            f"<span style='color:#e2e8f0'>{conf}/100</span>" if conf
            else "<span style='color:#64748b'>N/A</span>",
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            f"<span style='color:#94a3b8'>{run.duration_display}</span>",
            unsafe_allow_html=True,
        )

    with col6:
        st.markdown(
            f"<span style='color:#94a3b8'>{run.total_funding}</span>",
            unsafe_allow_html=True,
        )

    with col7:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("View", key=f"view_{run.run_id}", use_container_width=True):
                st.session_state["selected_run_id"] = run.run_id
                st.session_state["view_mode"] = "detail"
                st.rerun()
        with btn_col2:
            star_label = "★" if run.is_starred else "☆"
            if st.button(star_label, key=f"star_{run.run_id}", use_container_width=True):
                queries.toggle_star(run.run_id)
                st.rerun()


def render_run_card(run: ResearchRun) -> None:
    """
    Full detail view of a run — shown when user clicks 'View' on a row.
    Includes all research sections, charts, and action buttons.
    """
    # ── Header ────────────────────────────────────────────────────────────────
    star_label = "⭐ Starred" if run.is_starred else "☆ Star"
    h1, h2, h3, h4 = st.columns([3, 1, 1, 1])

    with h1:
        st.markdown(f"## 🏢 {run.company_name}")
        st.caption(
            f"Run ID: `{run.run_id}` · "
            f"{run.created_at_display} · "
            f"{run.duration_display} · "
            f"Sector: {run.sector_detected}"
        )

    with h2:
        if st.button(star_label, key=f"card_star_{run.run_id}", use_container_width=True):
            queries.toggle_star(run.run_id)
            st.rerun()

    with h3:
        st.download_button(
            "⬇️ Report",
            data=run.report_markdown,
            file_name=f"{run.company_slug}_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with h4:
        if st.button("🗑️ Delete", key=f"card_del_{run.run_id}", use_container_width=True):
            st.session_state[f"confirm_delete_{run.run_id}"] = True

    # Confirm delete dialog
    if st.session_state.get(f"confirm_delete_{run.run_id}"):
        st.warning(f"⚠️ Delete run for **{run.company_name}**? This cannot be undone.")
        yes, no = st.columns(2)
        with yes:
            if st.button("Yes, delete", key=f"yes_del_{run.run_id}"):
                queries.delete_run(run.run_id)
                st.session_state.pop(f"confirm_delete_{run.run_id}", None)
                st.session_state.pop("selected_run_id", None)
                st.session_state["view_mode"] = "list"
                st.success("Run deleted.")
                st.rerun()
        with no:
            if st.button("Cancel", key=f"no_del_{run.run_id}"):
                st.session_state.pop(f"confirm_delete_{run.run_id}", None)
                st.rerun()

    st.markdown("---")

    # ── Risk Summary ──────────────────────────────────────────────────────────
    if run.risk_scorecard and "error" not in run.risk_scorecard:
        from ui.components.risk_chart import radar_chart, gauge_chart, risk_summary_cards

        st.markdown("### 📊 Risk Scorecard")

        cards = risk_summary_cards(run.risk_scorecard)
        cols = st.columns(5)
        for col, card in zip(cols, cards):
            with col:
                st.markdown(
                    f"<div style='background:#1e293b;border-radius:8px;padding:0.8rem;"
                    f"border-left:3px solid {card['color']}'>"
                    f"<div style='font-size:1.5rem;font-weight:800;color:{card['color']}'>"
                    f"{card['score']}/10</div>"
                    f"<div style='font-size:0.75rem;color:#94a3b8'>{card['icon']} {card['title']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        rc, gc = st.columns([3, 2])
        with rc:
            st.plotly_chart(
                radar_chart(run.risk_scorecard, run.company_name),
                use_container_width=True,
            )
        with gc:
            st.plotly_chart(
                gauge_chart(run.risk_scorecard, run.company_name),
                use_container_width=True,
            )

    # ── Key Metrics Row ───────────────────────────────────────────────────────
    st.markdown("### 📌 Key Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Funding", run.total_funding)
    with m2:
        founders = run.team_data.get("founders", [])
        st.metric("Founders Found", len(founders))
    with m3:
        stage = run.seed_data.get("stage", "Unknown")
        st.metric("Stage", stage)
    with m4:
        st.metric("Market Position", run.market_position)
    with m5:
        docs = f"{run.documents_uploaded} file(s)" if run.has_documents else "None"
        st.metric("Documents", docs)

    st.markdown("---")

    # ── Research Sections (collapsible) ───────────────────────────────────────
    st.markdown("### 🔬 Research Data")

    sections = [
        ("👥 Team & Leadership",   run.team_data),
        ("💰 Funding & Investors", run.investor_data),
        ("📰 Press & Sentiment",   run.press_data),
        ("📊 Financial Signals",   run.financials_data),
        ("⚙️ Tech Stack",          run.tech_stack_data),
        ("📱 Social & Brand",      run.social_data),
        ("🏆 Competitor Intel",    run.competitor_data),
        ("🔍 Validation Notes",    run.validation_notes),
    ]

    for label, data in sections:
        if data and "error" not in data:
            with st.expander(label):
                st.json(data, expanded=False)

    # ── Full Report ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📄 Full Report")

    if run.has_documents:
        st.info(f"📎 This report was cross-referenced with {run.documents_uploaded} uploaded document(s): "
                f"{', '.join(run.doc_names)}")

    if run.report_markdown:
        with st.expander("📖 View Full Report", expanded=True):
            st.markdown(run.report_markdown)
    else:
        st.warning("No report markdown available for this run.")

    # ── LangSmith Trace ───────────────────────────────────────────────────────
    if run.langsmith_trace_url:
        st.markdown("---")
        st.markdown(
            f"🔭 [View LangSmith Trace]({run.langsmith_trace_url})",
            unsafe_allow_html=False,
        )

    # ── Notes ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📝 Notes")
    new_notes = st.text_area(
        "Add notes about this run",
        value=run.notes,
        key=f"notes_{run.run_id}",
        placeholder="Your observations, next steps, follow-up questions...",
        height=100,
    )
    if st.button("Save Notes", key=f"save_notes_{run.run_id}"):
        queries.update_run_notes(run.run_id, new_notes)
        st.success("Notes saved!")

    # ── Errors ────────────────────────────────────────────────────────────────
    if run.errors:
        with st.expander(f"⚠️ {len(run.errors)} agent error(s)"):
            for err in run.errors:
                st.caption(err)