"""
main.py — IntelliDD Pro Streamlit frontend.

Usage:
    uv run streamlit run main.py

Phase 3 features:
  Company URL input
  Document upload (PDF, CSV, XLSX, TXT)
  Real-time pipeline status display
  Full report rendering in Markdown
  Risk radar chart + DD confidence gauge
  Risk dimension cards (5 metrics)
  Competitor summary table
  JSON artifact download buttons
"""

import json
import tempfile
import time
import uuid
from pathlib import Path
from persistence.db import init_db
from pipeline.runner import run_due_diligence

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="IntelliDD Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# ── Imports ───────────────────────────────────────────────────────────────────
import config
from pipeline.graph import dd_graph
from pipeline.state import initial_state
from ui.components.risk_chart import radar_chart, gauge_chart, risk_summary_cards


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark theme overrides */
    .main { background-color: #0f172a; }
    .stApp { background-color: #0f172a; }

    /* Header banner */
    .intellidd-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border: 1px solid #1d63db;
        border-radius: 12px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
    }
    .intellidd-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #e2e8f0;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .intellidd-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 0.3rem;
    }
    .intellidd-badge {
        display: inline-block;
        background: rgba(29, 99, 219, 0.2);
        border: 1px solid #1d63db;
        color: #60a5fa;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.75rem;
        margin-right: 0.4rem;
        margin-top: 0.6rem;
    }

    /* Risk cards */
    .risk-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1rem;
        border-left: 4px solid #1d63db;
        margin-bottom: 0.5rem;
    }
    .risk-card-score {
        font-size: 1.8rem;
        font-weight: 800;
        color: #e2e8f0;
    }
    .risk-card-label {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.1rem;
    }

    /* Section divider */
    .section-header {
        border-bottom: 2px solid #1d63db;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 700;
    }

    /* Status badges */
    .status-running  { color: #f59e0b; }
    .status-complete { color: #22c55e; }
    .status-failed   { color: #ef4444; }

    /* Competitor table */
    .comp-table { width: 100%; border-collapse: collapse; }
    .comp-table th { background: #1e3a5f; color: #e2e8f0; padding: 0.6rem 1rem; text-align: left; }
    .comp-table td { padding: 0.5rem 1rem; border-bottom: 1px solid #1e293b; color: #cbd5e1; }
    .comp-table tr:hover td { background: #1e293b; }

    /* Upload area */
    .upload-note {
        background: rgba(29, 99, 219, 0.1);
        border: 1px dashed #1d63db;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        color: #93c5fd;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="intellidd-header">
    <div class="intellidd-title">🧠 IntelliDD Pro</div>
    <div class="intellidd-subtitle">AI-Powered Multi-Agent Due Diligence Intelligence Platform</div>
    <div style="margin-top: 0.8rem">
        <span class="intellidd-badge">LangGraph</span>
        <span class="intellidd-badge">7 Agents</span>
        <span class="intellidd-badge">Risk Scoring</span>
        <span class="intellidd-badge">Competitor Intel</span>
        <span class="intellidd-badge">Document RAG</span>
        <span class="intellidd-badge">100% Free Tier</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar: Config warnings ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    warnings = config.validate_config()
    if not warnings:
        st.success("All APIs configured ✅")
    else:
        for w in warnings:
            if "CRITICAL" in w:
                st.error(w)
            elif "⚠️" in w:
                st.warning(w)
            else:
                st.info(w)

    st.markdown("---")
    st.markdown("### 📘 How it works")
    st.markdown("""
1. Enter a company URL
2. (Optional) Upload documents
3. Click **Run Due Diligence**
4. 7 AI agents research in parallel
5. Risk scored across 5 dimensions
6. Full investment report generated
    """)


# ── Main Input Section ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Research Target</div>', unsafe_allow_html=True)

col_url, col_btn = st.columns([4, 1])

with col_url:
    company_url = st.text_input(
        "Company URL",
        placeholder="https://stripe.com",
        help="Enter the full URL of the company's homepage",
        label_visibility="collapsed",
    )

with col_btn:
    run_button = st.button(
        "🚀 Run Due Diligence",
        type="primary",
        use_container_width=True,
        disabled=not company_url.strip(),
    )

# ── Document Upload Section ───────────────────────────────────────────────────
st.markdown('<div class="section-header">📄 Upload Documents (Optional)</div>', unsafe_allow_html=True)

st.markdown("""
<div class="upload-note">
    📎 Upload pitch decks, financial models, or any company documents to cross-reference
    with web research. The RAG agent will extract relevant context and include it in the report.
    <br/><br/>
    Supported: <strong>PDF</strong> (pitch decks, reports) · <strong>CSV/XLSX</strong> (financial models) · <strong>TXT</strong> (notes)
</div>
""", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload Documents",
    type=["pdf", "csv", "xlsx", "xls", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    help="Upload pitch decks, financial models, or any company documents",
)

if uploaded_files:
    st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
    for f in uploaded_files:
        size_kb = round(f.size / 1024, 1)
        st.markdown(f"  - 📄 `{f.name}` ({size_kb} KB)")


# ── Pipeline Execution ────────────────────────────────────────────────────────
if run_button and company_url.strip():

    # Validate URL format
    url = company_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Save uploaded files to temp directory
    saved_file_paths = []
    if uploaded_files:
        tmp_dir = Path(tempfile.mkdtemp())
        for uf in uploaded_files:
            tmp_path = tmp_dir / uf.name
            tmp_path.write_bytes(uf.read())
            saved_file_paths.append(str(tmp_path))

    # Generate run identifiers
    run_id    = str(uuid.uuid4())[:8]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    company_slug = (
        url.replace("https://", "").replace("http://", "")
        .replace("www.", "").split("/")[0].split(".")[0].lower()
    )
    output_dir = str(Path(config.OUTPUTS_DIR) / f"{company_slug}_{timestamp}_{run_id}")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ── Progress UI ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">⚡ Pipeline Running</div>', unsafe_allow_html=True)

    progress_bar    = st.progress(0, text="Initializing pipeline...")
    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.metric("Run ID", run_id)
    with status_col2:
        st.metric("Target", company_slug.title())
    with status_col3:
        docs_label = f"{len(saved_file_paths)} file(s)" if saved_file_paths else "None"
        st.metric("Documents", docs_label)

    log_container = st.empty()
    log_messages  = []

    def add_log(msg: str):
        log_messages.append(f"`{time.strftime('%H:%M:%S')}` {msg}")
        log_container.markdown("\n\n".join(log_messages[-10:]))  # show last 10

    add_log(f"🚀 Starting pipeline for: **{url}**")
    if saved_file_paths:
        add_log(f"📁 {len(saved_file_paths)} document(s) will be processed via RAG")

    progress_bar.progress(10, text="Stage 1: Crawling company website...")
    add_log("🌱 Seed Crawler: scraping homepage...")

    # ── Build initial state + run graph ─────────────────────────────────────
    try:
        # Run the full LangGraph pipeline
        start_time = time.time()

        # We can't stream node-by-node in this simple version,
        # so we show progress updates before/after key stages
        progress_bar.progress(20, text="Stage 1: Seed Crawling...")
        add_log("🌱 Extracting company profile...")

        final_state = run_due_diligence(
            company_url=url,
            uploaded_files=saved_file_paths,
        )

        elapsed = round(time.time() - start_time, 1)
        progress_bar.progress(100, text="✅ Pipeline complete!")
        add_log(f"✅ **Pipeline completed in {elapsed}s**")

        if saved_file_paths:
            doc_context = final_state.get("doc_context", "")
            if doc_context:
                add_log(f"📄 Document RAG: context extracted and included in report")
            else:
                add_log("⚠️ Document RAG: no relevant content found in uploaded files")

    except Exception as e:
        progress_bar.progress(100, text="❌ Pipeline failed")
        st.error(f"Pipeline failed: {str(e)}")
        st.stop()

    # ── Results Display ──────────────────────────────────────────────────────
    pipeline_status = final_state.get("pipeline_status", "unknown")
    errors = final_state.get("errors", [])

    if pipeline_status == "completed":
        st.success(f"✅ Due diligence complete in {final_state.get('duration_seconds', 0)}s")
    else:
        st.warning(f"⚠️ Pipeline finished with status: {pipeline_status}")

    if errors:
        with st.expander(f"⚠️ {len(errors)} agent error(s) — pipeline continued"):
            for err in errors:
                st.caption(err)

    # ── Risk Dashboard ───────────────────────────────────────────────────────
    risk_scorecard = final_state.get("risk_scorecard", {})

    if risk_scorecard and "error" not in risk_scorecard:
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Risk Scorecard</div>', unsafe_allow_html=True)

        company_name = final_state.get("seed_data", {}).get("company_name", company_slug.title())

        # Risk dimension cards
        cards = risk_summary_cards(risk_scorecard)
        cols = st.columns(5)
        for col, card in zip(cols, cards):
            with col:
                st.markdown(f"""
                <div class="risk-card" style="border-left-color: {card['color']}">
                    <div class="risk-card-score" style="color: {card['color']}">{card['score']}/10</div>
                    <div class="risk-card-label">{card['icon']} {card['title']}</div>
                    <div style="color: #64748b; font-size: 0.7rem; margin-top: 0.3rem">{card['severity']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Radar + gauge charts
        chart_col1, chart_col2 = st.columns([3, 2])
        with chart_col1:
            st.plotly_chart(
                radar_chart(risk_scorecard, company_name),
                use_container_width=True,
            )
        with chart_col2:
            st.plotly_chart(
                gauge_chart(risk_scorecard, company_name),
                use_container_width=True,
            )

        # Risk detail expander
        with st.expander("📋 Risk Detail Breakdown"):
            for card in cards:
                st.markdown(f"**{card['icon']} {card['title']} — {card['score']}/10 [{card['severity']}]**")
                if card["key_factors"]:
                    for factor in card["key_factors"]:
                        st.markdown(f"  - {factor}")
                if card["evidence"]:
                    st.caption(f"Evidence: {card['evidence']}")
                if card["mitigation"]:
                    st.caption(f"Mitigation: {card['mitigation']}")
                st.markdown("---")

    # ── Competitor Summary ───────────────────────────────────────────────────
    competitor_data = final_state.get("competitor_data", {})
    competitors = competitor_data.get("competitors", [])

    if competitors:
        st.markdown("---")
        st.markdown('<div class="section-header">🏆 Competitor Landscape</div>', unsafe_allow_html=True)

        meta_col1, meta_col2, meta_col3 = st.columns(3)
        with meta_col1:
            st.metric("Market Position", competitor_data.get("market_position", "Unknown"))
        with meta_col2:
            st.metric("Differentiation Score", f"{competitor_data.get('differentiation_score', 'N/A')}/100")
        with meta_col3:
            st.metric("Competitors Found", len(competitors))

        # Competitor table
        table_rows = []
        for c in competitors:
            table_rows.append({
                "Company":       c.get("name", "Unknown"),
                "Stage":         c.get("funding_stage", "Unknown"),
                "Funding":       c.get("funding_total", "Unknown"),
                "Employees":     c.get("employee_estimate", "Unknown"),
                "Overlap Score": f"{c.get('overlap_score', '?')}/10",
                "Key Diff":      c.get("key_differentiator", "")[:60] + "...",
            })

        if table_rows:
            import pandas as pd
            st.dataframe(
                pd.DataFrame(table_rows),
                use_container_width=True,
                hide_index=True,
            )

        st.caption(f"🎯 {competitor_data.get('moat_assessment', '')}")

    # ── Full Report ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">📄 Due Diligence Report</div>', unsafe_allow_html=True)

    doc_context_used = bool(final_state.get("doc_context", ""))
    if doc_context_used:
        st.info("📎 This report includes context from uploaded documents (cross-referenced with web research)")

    report_md = final_state.get("report_markdown", "")
    if report_md and not report_md.startswith("# Report Generation Failed"):
        st.markdown(report_md)
    else:
        st.error("Report generation failed. Check agent errors above.")

    # ── Downloads ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header">⬇️ Download Artifacts</div>', unsafe_allow_html=True)

    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)

    with dl_col1:
        st.download_button(
            "📄 Download Report (MD)",
            data=report_md,
            file_name=f"{company_slug}_dd_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with dl_col2:
        if risk_scorecard:
            st.download_button(
                "📊 Risk Scorecard (JSON)",
                data=json.dumps(risk_scorecard, indent=2),
                file_name=f"{company_slug}_risk_scorecard.json",
                mime="application/json",
                use_container_width=True,
            )

    with dl_col3:
        if competitors:
            st.download_button(
                "🏆 Competitor Intel (JSON)",
                data=json.dumps(competitor_data, indent=2),
                file_name=f"{company_slug}_competitors.json",
                mime="application/json",
                use_container_width=True,
            )

    with dl_col4:
        full_output = {
            "run_id":           run_id,
            "company_url":      url,
            "pipeline_status":  pipeline_status,
            "duration_seconds": final_state.get("duration_seconds", 0),
            "company_profile":  final_state.get("seed_data", {}),
            "team":             final_state.get("team_data", {}),
            "investors":        final_state.get("investor_data", {}),
            "press":            final_state.get("press_data", {}),
            "financials":       final_state.get("financials_data", {}),
            "tech_stack":       final_state.get("tech_stack_data", {}),
            "social":           final_state.get("social_data", {}),
            "competitors":      final_state.get("competitor_data", {}),
            "risk_scorecard":   final_state.get("risk_scorecard", {}),
        }
        st.download_button(
            "📦 Full Output (JSON)",
            data=json.dumps(full_output, indent=2),
            file_name=f"{company_slug}_full_output.json",
            mime="application/json",
            use_container_width=True,
        )

    st.caption(f"📁 All artifacts saved to: `{output_dir}`")