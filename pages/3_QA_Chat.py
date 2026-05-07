"""
pages/3_QA_Chat.py — ReAct Q&A Chat Interface.

Features:
  Chat with any past run loaded from History
  Chat with the most recently generated report
  Real-time streaming-style response display
  Tool call log panel (shows which tools were used)
  Suggested questions based on the report
  Full chat history preserved in session state
  Clear chat and switch run buttons
"""

import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliDD Pro — Q&A Chat",
    page_icon="💬",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main  { background-color: #0f172a; }
    .stApp { background-color: #0f172a; }

    .chat-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border: 1px solid #1d63db;
        border-radius: 12px;
        padding: 1.2rem 1.8rem;
        margin-bottom: 1rem;
    }
    .context-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        border-left: 3px solid #1d63db;
    }
    .tool-log {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 0.8rem;
        font-family: 'Courier New', monospace;
        font-size: 0.75rem;
        color: #64748b;
        max-height: 200px;
        overflow-y: auto;
    }
    .tool-badge {
        display: inline-block;
        background: rgba(29, 99, 219, 0.2);
        border: 1px solid #1d63db;
        color: #60a5fa;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        margin: 2px;
    }
    .suggested-q {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.5rem 0.8rem;
        font-size: 0.82rem;
        color: #94a3b8;
        cursor: pointer;
        margin-bottom: 0.3rem;
    }
    .suggested-q:hover { border-color: #1d63db; color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
from persistence.db import init_db
from persistence.queries import list_runs, get_run
from qa.qa_graph import build_qa_agent, ask_question, build_run_context_from_db

init_db()

# ── Session state init ────────────────────────────────────────────────────────
if "qa_chat_history"    not in st.session_state:
    st.session_state["qa_chat_history"]    = []
if "qa_run_id"          not in st.session_state:
    st.session_state["qa_run_id"]          = None
if "qa_agent"           not in st.session_state:
    st.session_state["qa_agent"]           = None
if "qa_run_context"     not in st.session_state:
    st.session_state["qa_run_context"]     = None
if "qa_tool_log"        not in st.session_state:
    st.session_state["qa_tool_log"]        = []
if "qa_pending_question" not in st.session_state:
    st.session_state["qa_pending_question"] = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="chat-header">
    <div style="font-size:1.6rem;font-weight:800;color:#e2e8f0">
        💬 Q&A Chat — Ask Anything About a Company
    </div>
    <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem">
        ReAct agent with 4 tools: Report Search · Web Search · Risk Detail · History Compare
    </div>
</div>
""", unsafe_allow_html=True)

# ── Run Selector ──────────────────────────────────────────────────────────────
all_runs = list_runs(limit=30)

if not all_runs:
    st.info(
        "📭 No research runs found. Go to the **Research** page to run your "
        "first due diligence, then come back to chat with the report!"
    )
    st.stop()

# Build selector options
run_options = {
    f"{r.company_name}  ·  {r.created_at_display[:16]}  ·  Risk: {r.overall_risk_score}/10": r.run_id
    for r in all_runs
}
run_labels = list(run_options.keys())

sel_col, clear_col = st.columns([4, 1])
with sel_col:
    selected_label = st.selectbox(
        "Select a research run to chat with",
        run_labels,
        key="run_selector",
        label_visibility="collapsed",
    )
with clear_col:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["qa_chat_history"] = []
        st.session_state["qa_tool_log"]     = []
        st.rerun()

selected_run_id = run_options[selected_label]

# Reload agent if run changed
if selected_run_id != st.session_state["qa_run_id"]:
    with st.spinner("Loading research context..."):
        run = get_run(selected_run_id)
        if run:
            ctx   = build_run_context_from_db(run)
            agent = build_qa_agent(ctx)
            st.session_state["qa_run_id"]      = selected_run_id
            st.session_state["qa_agent"]        = agent
            st.session_state["qa_run_context"]  = ctx
            st.session_state["qa_chat_history"] = []
            st.session_state["qa_tool_log"]     = []
            st.session_state["qa_pending_question"] = None

# ── Context Banner ────────────────────────────────────────────────────────────
ctx = st.session_state.get("qa_run_context")
if ctx:
    risk_score = ctx.get("overall_risk_score", "N/A")
    confidence = ctx.get("dd_confidence_score", "N/A")
    has_docs   = ctx.get("has_documents", False)

    risk_color = (
        "#22c55e" if isinstance(risk_score, int) and risk_score <= 3
        else "#f59e0b" if isinstance(risk_score, int) and risk_score <= 6
        else "#ef4444"
    )

    st.markdown(
        f'<div class="context-card">'
        f'<span style="font-weight:700;color:#e2e8f0">{ctx["company_name"]}</span>'
        f'<span style="color:#64748b;font-size:0.8rem"> · {ctx["sector_label"]}</span>'
        f'<span style="margin-left:1rem;color:{risk_color};font-weight:700">'
        f'Risk {risk_score}/10</span>'
        f'<span style="margin-left:1rem;color:#60a5fa">Confidence {confidence}/100</span>'
        f'{"<span style=margin-left:1rem;color:#a78bfa>📄 Docs available</span>" if has_docs else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Main layout: Chat + Tool Log ──────────────────────────────────────────────
chat_col, log_col = st.columns([3, 1])

# ── Tool Log Panel ────────────────────────────────────────────────────────────
with log_col:
    st.markdown("**🔧 Agent Tool Log**")
    st.caption("Shows which tools the agent used for each answer")

    tool_log = st.session_state.get("qa_tool_log", [])
    if tool_log:
        for entry in reversed(tool_log[-8:]):  # show last 8 tool calls
            q_short = entry.get("question", "")[:30]
            tools   = entry.get("tools_used", [])
            st.markdown(
                f"<div class='tool-log'>"
                f"<div style='color:#94a3b8'>Q: {q_short}...</div>"
                + "".join(
                    f"<span class='tool-badge'>{t}</span>" for t in tools
                )
                + "</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div class='tool-log'>No tool calls yet.<br/>Ask a question to see which tools the agent uses.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**💡 Suggested Questions**")

    company_name = ctx["company_name"] if ctx else "the company"
    suggestions = [
        f"Who are the founders of {company_name}?",
        "What is the biggest risk and why?",
        "What is the financial risk score breakdown?",
        f"Who are {company_name}'s main competitors?",
        "What is the total funding raised?",
        "Has anything changed since last time?",
        "What is the market position and differentiation score?",
        "What are the top 3 positive signals?",
        "How does the tech stack compare to sector standards?",
        "What are the critical data gaps in this report?",
    ]

    for suggestion in suggestions:
        if st.button(
            suggestion,
            key=f"sug_{suggestion[:20]}",
            use_container_width=True,
        ):
            st.session_state["qa_pending_question"] = suggestion
            st.rerun()

# ── Chat Interface ────────────────────────────────────────────────────────────
with chat_col:
    # Display existing chat history
    chat_history = st.session_state.get("qa_chat_history", [])

    for msg in chat_history:
        role    = msg["role"]
        content = msg["content"]
        tools   = msg.get("tools_used", [])

        with st.chat_message(role):
            st.markdown(content)
            if tools and role == "assistant":
                tool_html = " ".join(
                    f"<span class='tool-badge'>🔧 {t}</span>" for t in tools
                )
                st.markdown(
                    f"<div style='margin-top:0.4rem'>{tool_html}</div>",
                    unsafe_allow_html=True,
                )

    # ── Handle pending question (from suggestion buttons) ─────────────────────
    pending = st.session_state.get("qa_pending_question")
    if pending:
        st.session_state["qa_pending_question"] = None
        user_question = pending
    else:
        user_question = None

    # ── Chat input ────────────────────────────────────────────────────────────
    typed_question = st.chat_input(
        placeholder=f"Ask anything about {company_name}...",
        key="qa_input",
    )

    if typed_question:
        user_question = typed_question

    # ── Process question ──────────────────────────────────────────────────────
    if user_question and st.session_state.get("qa_agent"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)

        # Add to history
        st.session_state["qa_chat_history"].append({
            "role":    "user",
            "content": user_question,
        })

        # Run the agent
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                agent  = st.session_state["qa_agent"]
                result = ask_question(
                    agent=agent,
                    question=user_question,
                    chat_history=st.session_state["qa_chat_history"][:-1],
                )

            answer     = result["answer"]
            tools_used = result["tools_used"]
            error      = result["error"]

            # Display answer
            if error and error != "rate_limit":
                st.error(f"Agent error: {error}")
            else:
                st.markdown(answer)

            # Show tools used inline
            if tools_used:
                tool_html = " ".join(
                    f"<span class='tool-badge'>🔧 {t}</span>" for t in tools_used
                )
                st.markdown(
                    f"<div style='margin-top:0.5rem'>{tool_html}</div>",
                    unsafe_allow_html=True,
                )

            # Detailed tool call expander
            tool_calls = result.get("tool_calls", [])
            if tool_calls:
                with st.expander(f"🔍 Tool call details ({len(tool_calls)} calls)"):
                    for tc in tool_calls:
                        st.markdown(f"**Tool:** `{tc['tool']}`")
                        st.caption(f"Output preview: {tc['output']}")
                        st.markdown("---")

        # Save to history
        st.session_state["qa_chat_history"].append({
            "role":       "assistant",
            "content":    answer,
            "tools_used": tools_used,
        })

        # Update tool log
        st.session_state["qa_tool_log"].append({
            "question":   user_question,
            "tools_used": tools_used,
        })

        st.rerun()

    elif user_question and not st.session_state.get("qa_agent"):
        st.warning("Please select a research run above to start chatting.")