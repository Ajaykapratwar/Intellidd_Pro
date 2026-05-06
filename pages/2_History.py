"""
pages/2_History.py — Past research runs history and comparison page.

Features:
  List all past runs with key metrics
  Search across company names and reports
  Filter by sector, status, starred
  Full run detail view with risk charts
  Side-by-side comparison of two runs for the same company
  Star, note, tag, and delete runs
  Download reports from history
"""

import streamlit as st

from persistence.db import init_db, get_db_stats
from persistence import queries
from ui.components.report_card import render_run_card, render_run_summary_row
from ui.components.comparison_diff import render_comparison

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliDD Pro — History",
    page_icon="📚",
    layout="wide",
)

# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; }
    .hist-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border: 1px solid #1d63db;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .stat-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        border-left: 3px solid #1d63db;
        text-align: center;
    }
    .stat-number { font-size: 1.8rem; font-weight: 800; color: #60a5fa; }
    .stat-label  { font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; }
    .table-header {
        background: #1e3a5f;
        border-radius: 6px;
        padding: 0.5rem 0.8rem;
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hist-header">
    <div style="font-size:1.8rem;font-weight:800;color:#e2e8f0">
        📚 Research History
    </div>
    <div style="color:#94a3b8;font-size:0.9rem;margin-top:0.3rem">
        Browse, search, and compare all past due diligence runs
    </div>
</div>
""", unsafe_allow_html=True)

# ── DB Stats ──────────────────────────────────────────────────────────────────
stats = get_db_stats()
if "error" not in stats:
    s1, s2, s3, s4 = st.columns(4)
    stat_data = [
        (stats.get("total_runs", 0),       "Total Runs",        s1),
        (stats.get("unique_companies", 0),  "Companies Researched", s2),
        (stats.get("db_size_kb", 0),        "DB Size (KB)",      s3),
        (stats.get("latest_run", "—")[:16], "Latest Run",        s4),
    ]
    for value, label, col in stat_data:
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-number">{value}</div>'
                f'<div class="stat-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

st.markdown("<br/>", unsafe_allow_html=True)

# ── Initialize session state ──────────────────────────────────────────────────
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "list"   # "list" | "detail" | "compare"
if "selected_run_id" not in st.session_state:
    st.session_state["selected_run_id"] = None
if "compare_run_ids" not in st.session_state:
    st.session_state["compare_run_ids"] = []

# ── View Router ───────────────────────────────────────────────────────────────

# ── DETAIL VIEW ──────────────────────────────────────────────────────────────
if st.session_state["view_mode"] == "detail" and st.session_state["selected_run_id"]:
    if st.button("← Back to History"):
        st.session_state["view_mode"] = "list"
        st.session_state["selected_run_id"] = None
        st.rerun()

    run = queries.get_run(st.session_state["selected_run_id"])
    if run:
        render_run_card(run)
    else:
        st.error("Run not found. It may have been deleted.")
        st.session_state["view_mode"] = "list"


# ── COMPARE VIEW ─────────────────────────────────────────────────────────────
elif st.session_state["view_mode"] == "compare":
    if st.button("← Back to History"):
        st.session_state["view_mode"] = "list"
        st.session_state["compare_run_ids"] = []
        st.rerun()

    ids = st.session_state["compare_run_ids"]
    if len(ids) == 2:
        run_a = queries.get_run(ids[0])
        run_b = queries.get_run(ids[1])
        if run_a and run_b:
            render_comparison(run_a, run_b)
        else:
            st.error("One or both runs not found.")
    else:
        st.warning("Select exactly 2 runs to compare.")
        st.session_state["view_mode"] = "list"


# ── LIST VIEW ─────────────────────────────────────────────────────────────────
else:
    # ── Search + Filters ──────────────────────────────────────────────────────
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([3, 1.5, 1.5, 1.5])

    with filter_col1:
        search_query = st.text_input(
            "Search",
            placeholder="🔍 Search company name, sector, or report content...",
            label_visibility="collapsed",
        )
    with filter_col2:
        starred_only = st.checkbox("⭐ Starred only")
    with filter_col3:
        status_filter = st.selectbox(
            "Status",
            ["All", "completed", "failed"],
            label_visibility="collapsed",
        )
    with filter_col4:
        sort_order = st.selectbox(
            "Sort",
            ["Newest first", "Oldest first"],
            label_visibility="collapsed",
        )

    # ── Fetch runs ────────────────────────────────────────────────────────────
    if search_query.strip():
        runs = queries.search_runs(search_query.strip(), limit=50)
    else:
        status_arg = None if status_filter == "All" else status_filter
        runs = queries.list_runs(
            limit=50,
            starred_only=starred_only,
            status_filter=status_arg,
        )

    if sort_order == "Oldest first":
        runs = list(reversed(runs))

    if not runs:
        st.info(
            "No runs found. Head to the **Research** page to run your first due diligence!"
            if not search_query else f"No results for '{search_query}'."
        )
    else:
        # ── Company group selector (for compare) ──────────────────────────────
        companies = queries.get_all_company_slugs()
        if len(companies) > 0:
            with st.expander("🔄 Compare Two Runs (same company)"):
                company_options = {
                    f"{c['company_name']} ({c['run_count']} runs)": c["company_slug"]
                    for c in companies if c["run_count"] >= 2
                }
                if company_options:
                    selected_company_label = st.selectbox(
                        "Select company to compare",
                        list(company_options.keys()),
                    )
                    selected_slug = company_options[selected_company_label]
                    company_runs  = queries.get_runs_for_company(selected_slug)

                    run_options = {
                        f"{r.created_at_display} (Risk: {r.overall_risk_score}/10)": r.run_id
                        for r in company_runs
                    }
                    run_labels = list(run_options.keys())

                    cmp1, cmp2, cmp3 = st.columns([2, 2, 1])
                    with cmp1:
                        sel_a = st.selectbox("Run A (baseline)", run_labels, key="cmp_a")
                    with cmp2:
                        remaining = [l for l in run_labels if l != sel_a]
                        sel_b = st.selectbox("Run B (latest)", remaining or run_labels, key="cmp_b")
                    with cmp3:
                        st.markdown("<br/>", unsafe_allow_html=True)
                        if st.button("Compare →", use_container_width=True):
                            run_id_a = run_options[sel_a]
                            run_id_b = run_options.get(sel_b, run_options[run_labels[-1]])
                            if run_id_a != run_id_b:
                                st.session_state["compare_run_ids"] = [run_id_a, run_id_b]
                                st.session_state["view_mode"] = "compare"
                                st.rerun()
                            else:
                                st.warning("Select two different runs to compare.")
                else:
                    st.info("Run the same company at least twice to enable comparison.")

        st.markdown("---")

        # ── Table header ──────────────────────────────────────────────────────
        st.markdown(
            f"**{len(runs)} run(s) found**",
        )
        st.markdown("<br/>", unsafe_allow_html=True)

        header = st.columns([2.5, 1.2, 1.0, 1.0, 1.0, 1.0, 1.5])
        headers = ["Company", "Sector", "Risk", "Confidence", "Duration", "Funding", "Actions"]
        for col, h in zip(header, headers):
            col.markdown(f"**{h}**")

        st.markdown("---")

        # ── Runs list ─────────────────────────────────────────────────────────
        for run in runs:
            render_run_summary_row(run)
            st.markdown(
                "<hr style='border:none;border-top:1px solid #1e293b;margin:4px 0'>",
                unsafe_allow_html=True,
            )