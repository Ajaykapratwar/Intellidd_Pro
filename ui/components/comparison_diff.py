"""
ui/components/comparison_diff.py — Side-by-side run comparison component.

Compares two ResearchRun objects and highlights what changed.

Usage:
    from ui.components.comparison_diff import render_comparison
    render_comparison(run_a, run_b)
"""

import streamlit as st

from persistence.models import ResearchRun


def _diff_badge(val_a, val_b, higher_is_better: bool = False) -> str:
    """
    Returns a colored diff indicator between two comparable values.
    """
    try:
        a = float(str(val_a).replace("/10", "").replace("/100", ""))
        b = float(str(val_b).replace("/10", "").replace("/100", ""))
        if a == b:
            return "→ No change"
        delta = b - a
        if higher_is_better:
            color = "#22c55e" if delta > 0 else "#ef4444"
            arrow = "↑" if delta > 0 else "↓"
        else:
            # For risk scores: lower is better
            color = "#22c55e" if delta < 0 else "#ef4444"
            arrow = "↓" if delta < 0 else "↑"
        return f"<span style='color:{color}'>{arrow} {abs(delta):.1f}</span>"
    except Exception:
        if str(val_a) != str(val_b):
            return "<span style='color:#f59e0b'>Changed</span>"
        return "→ Same"


def render_comparison(run_a: ResearchRun, run_b: ResearchRun) -> None:
    """
    Render a full side-by-side comparison between two runs.

    Args:
        run_a: The earlier/baseline run (left side)
        run_b: The later/current run (right side)
    """
    st.markdown("## 🔄 Run Comparison")
    st.caption(
        f"Comparing **{run_a.created_at_display}** → **{run_b.created_at_display}**"
    )
    st.markdown("---")

    # ── Risk Score Comparison ─────────────────────────────────────────────────
    st.markdown("### 📊 Risk Score Changes")

    risk_dims = [
        ("Founder Risk",      "founder_risk",      False),
        ("Market Risk",       "market_risk",        False),
        ("Financial Risk",    "financial_risk",     False),
        ("Technical Risk",    "technical_risk",     False),
        ("Reputational Risk", "reputational_risk",  False),
    ]

    header = st.columns([2, 1.5, 1.5, 1.5])
    header[0].markdown("**Dimension**")
    header[1].markdown(f"**{run_a.created_at_display[:12]}**")
    header[2].markdown(f"**{run_b.created_at_display[:12]}**")
    header[3].markdown("**Change**")

    for label, key, higher_better in risk_dims:
        score_a = run_a.risk_scorecard.get(key, {}).get("score", "N/A")
        score_b = run_b.risk_scorecard.get(key, {}).get("score", "N/A")
        sev_a   = run_a.risk_scorecard.get(key, {}).get("severity", "")
        sev_b   = run_b.risk_scorecard.get(key, {}).get("severity", "")

        row = st.columns([2, 1.5, 1.5, 1.5])
        row[0].markdown(label)
        row[1].markdown(f"`{score_a}/10` {sev_a}")
        row[2].markdown(f"`{score_b}/10` {sev_b}")
        row[3].markdown(
            _diff_badge(score_a, score_b, higher_is_better=False),
            unsafe_allow_html=True,
        )

    # Overall scores
    st.markdown("---")
    overall_cols = st.columns([2, 1.5, 1.5, 1.5])
    overall_cols[0].markdown("**Overall Risk Score**")
    overall_cols[1].markdown(f"**{run_a.overall_risk_score}/10**")
    overall_cols[2].markdown(f"**{run_b.overall_risk_score}/10**")
    overall_cols[3].markdown(
        _diff_badge(run_a.overall_risk_score, run_b.overall_risk_score),
        unsafe_allow_html=True,
    )

    conf_cols = st.columns([2, 1.5, 1.5, 1.5])
    conf_cols[0].markdown("**DD Confidence Score**")
    conf_cols[1].markdown(f"**{run_a.dd_confidence_score}/100**")
    conf_cols[2].markdown(f"**{run_b.dd_confidence_score}/100**")
    conf_cols[3].markdown(
        _diff_badge(run_a.dd_confidence_score, run_b.dd_confidence_score, higher_is_better=True),
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Key Facts Comparison ──────────────────────────────────────────────────
    st.markdown("### 📌 Key Facts")

    facts = [
        ("Total Funding",     run_a.investor_data.get("total_funding_usd", "Unknown"),
                              run_b.investor_data.get("total_funding_usd", "Unknown")),
        ("Last Round",        run_a.investor_data.get("last_round_type", "Unknown"),
                              run_b.investor_data.get("last_round_type", "Unknown")),
        ("Market Position",   run_a.competitor_data.get("market_position", "Unknown"),
                              run_b.competitor_data.get("market_position", "Unknown")),
        ("Differentiation",   run_a.competitor_data.get("differentiation_score", "N/A"),
                              run_b.competitor_data.get("differentiation_score", "N/A")),
        ("Press Sentiment",   run_a.press_data.get("overall_sentiment", "Unknown"),
                              run_b.press_data.get("overall_sentiment", "Unknown")),
        ("Brand Score",       run_a.social_data.get("overall_brand_score", "N/A"),
                              run_b.social_data.get("overall_brand_score", "N/A")),
        ("Revenue Estimate",  run_a.financials_data.get("revenue_estimate", "Unknown"),
                              run_b.financials_data.get("revenue_estimate", "Unknown")),
        ("Stage",             run_a.seed_data.get("stage", "Unknown"),
                              run_b.seed_data.get("stage", "Unknown")),
        ("Tech Modernity",    run_a.tech_stack_data.get("tech_stack_modernity_score", "N/A"),
                              run_b.tech_stack_data.get("tech_stack_modernity_score", "N/A")),
        ("Competitors Found", len(run_a.competitor_data.get("competitors", [])),
                              len(run_b.competitor_data.get("competitors", []))),
    ]

    fh = st.columns([2, 2, 2, 1.5])
    fh[0].markdown("**Field**")
    fh[1].markdown(f"**Run A** ({run_a.created_at_display[:12]})")
    fh[2].markdown(f"**Run B** ({run_b.created_at_display[:12]})")
    fh[3].markdown("**Changed?**")

    for label, val_a, val_b in facts:
        row = st.columns([2, 2, 2, 1.5])
        row[0].markdown(label)
        row[1].markdown(f"`{val_a}`")
        row[2].markdown(f"`{val_b}`")
        changed = str(val_a) != str(val_b)
        row[3].markdown(
            "<span style='color:#f59e0b'>⚡ Changed</span>" if changed
            else "<span style='color:#64748b'>— Same</span>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Validation Gap Comparison ─────────────────────────────────────────────
    st.markdown("### 🔍 Data Quality Comparison")

    q1, q2 = st.columns(2)
    with q1:
        st.markdown(f"**Run A** — Quality: `{run_a.validation_notes.get('overall_data_quality', 'N/A')}/10`")
        gaps_a = run_a.validation_notes.get("critical_gaps", [])
        if gaps_a:
            for g in gaps_a[:5]:
                st.markdown(f"  - {g}")
        else:
            st.markdown("  No critical gaps recorded")

    with q2:
        st.markdown(f"**Run B** — Quality: `{run_b.validation_notes.get('overall_data_quality', 'N/A')}/10`")
        gaps_b = run_b.validation_notes.get("critical_gaps", [])
        if gaps_b:
            for g in gaps_b[:5]:
                st.markdown(f"  - {g}")
        else:
            st.markdown("  No critical gaps recorded")

    st.markdown("---")

    # ── Download both reports ─────────────────────────────────────────────────
    st.markdown("### ⬇️ Download Reports")
    dl1, dl2 = st.columns(2)
    with dl1:
        st.download_button(
            f"📄 Run A — {run_a.created_at_display[:12]}",
            data=run_a.report_markdown,
            file_name=f"{run_a.company_slug}_runA_{run_a.run_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with dl2:
        st.download_button(
            f"📄 Run B — {run_b.created_at_display[:12]}",
            data=run_b.report_markdown,
            file_name=f"{run_b.company_slug}_runB_{run_b.run_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )