"""
pages/4_Monitoring.py — Company monitoring management page.

Features:
  List all monitored companies with status + next run time
  Add new monitor (URL, frequency, email, Slack webhook)
  Toggle monitor on/off without deleting
  Trigger an immediate manual run
  Delete a monitor
  Change events history with severity filtering
  Alert channel configuration status
"""

import streamlit as st
from datetime import datetime

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IntelliDD Pro — Monitoring",
    page_icon="📡",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main  { background-color: #0f172a; }
    .stApp { background-color: #0f172a; }
    .mon-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border: 1px solid #1d63db;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .monitor-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #1d63db;
    }
    .monitor-card.inactive { border-left-color: #334155; }
    .event-row-high   { border-left: 3px solid #ef4444; padding: 8px 12px; margin: 4px 0; background: rgba(239,68,68,0.05); border-radius: 4px; }
    .event-row-medium { border-left: 3px solid #f59e0b; padding: 8px 12px; margin: 4px 0; background: rgba(245,158,11,0.05); border-radius: 4px; }
    .event-row-low    { border-left: 3px solid #22c55e; padding: 8px 12px; margin: 4px 0; background: rgba(34,197,94,0.05); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Imports ───────────────────────────────────────────────────────────────────
import config
from persistence.db import init_db
from persistence.queries import (
    list_monitors, get_monitor, delete_monitor,
    toggle_monitor_active, list_change_events,
)
from monitoring.scheduler import get_scheduler, FREQUENCY_LABELS, FREQUENCY_OPTIONS

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
scheduler = get_scheduler()
if not scheduler.is_running:
    scheduler.start()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mon-header">
    <div style="font-size:1.8rem;font-weight:800;color:#e2e8f0">
        📡 Company Monitoring
    </div>
    <div style="color:#94a3b8;font-size:0.85rem;margin-top:0.3rem">
        Schedule automatic re-research and receive alerts when significant changes are detected
    </div>
</div>
""", unsafe_allow_html=True)

# ── Scheduler status banner ───────────────────────────────────────────────────
if scheduler.is_running:
    st.success("✅ Scheduler is running — monitored companies will be automatically re-researched")
else:
    st.error("❌ Scheduler is not running. Restart the app to re-enable monitoring.")

# ── Alert channels config ─────────────────────────────────────────────────────
with st.expander("🔔 Alert Channel Configuration", expanded=False):
    ac1, ac2 = st.columns(2)
    with ac1:
        st.markdown("**📧 Email (Gmail SMTP)**")
        email_status = "✅ Configured" if config.ALERT_EMAIL_FROM else "❌ Not configured"
        st.markdown(f"Status: {email_status}")
        if not config.ALERT_EMAIL_FROM:
            st.code("ALERT_EMAIL_FROM=your_gmail@gmail.com\nALERT_EMAIL_PASSWORD=your_app_password")
            st.caption("Get a Gmail App Password at myaccount.google.com/apppasswords")
    with ac2:
        st.markdown("**💬 Slack Webhook**")
        slack_status = "✅ Configured (global)" if config.ALERT_SLACK_WEBHOOK else "ℹ️ Set per-monitor below"
        st.markdown(f"Status: {slack_status}")
        if not config.ALERT_SLACK_WEBHOOK:
            st.code("ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/...")
            st.caption("Create an incoming webhook at api.slack.com/apps")

st.markdown("---")

# ── Add new monitor ───────────────────────────────────────────────────────────
st.markdown("### ➕ Add New Monitor")

with st.form("add_monitor_form", clear_on_submit=True):
    f1, f2 = st.columns([3, 1])
    with f1:
        new_url = st.text_input(
            "Company URL",
            placeholder="https://stripe.com",
            help="The company homepage to monitor",
        )
    with f2:
        new_freq = st.selectbox(
            "Frequency",
            list(FREQUENCY_OPTIONS.keys()),
            format_func=lambda k: FREQUENCY_LABELS[k],
        )

    f3, f4 = st.columns(2)
    with f3:
        new_email = st.text_input(
            "Alert Email (optional)",
            placeholder="analyst@yourfirm.com",
        )
    with f4:
        new_slack = st.text_input(
            "Slack Webhook (optional)",
            placeholder="https://hooks.slack.com/services/...",
        )

    submitted = st.form_submit_button(
        "📡 Add Monitor",
        type="primary",
        use_container_width=True,
    )

    if submitted:
        if not new_url.strip():
            st.error("Please enter a company URL.")
        else:
            url = new_url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            # Derive company name from URL
            company_name = (
                url.replace("https://", "").replace("http://", "")
                .replace("www.", "").split("/")[0].split(".")[0].title()
            )

            monitor_id = scheduler.add_monitor(
                company_url=url,
                company_name=company_name,
                frequency=new_freq,
                alert_email=new_email.strip() or None,
                alert_slack_webhook=new_slack.strip() or None,
            )

            if monitor_id:
                st.success(
                    f"✅ Monitor added for **{company_name}** "
                    f"({FREQUENCY_LABELS[new_freq]}). "
                    f"Monitor ID: `{monitor_id}`"
                )
                st.rerun()
            else:
                st.error("Failed to add monitor. Check logs.")

st.markdown("---")

# ── Active monitors ───────────────────────────────────────────────────────────
st.markdown("### 📋 Active Monitors")

monitors = list_monitors(active_only=False)

if not monitors:
    st.info(
        "No monitors configured yet. Add one above to start tracking a company automatically."
    )
else:
    # Header row
    hcols = st.columns([2.5, 1.2, 1.0, 1.5, 1.5, 2.0])
    headers = ["Company", "Frequency", "Status", "Last Run", "Total Runs", "Actions"]
    for col, h in zip(hcols, headers):
        col.markdown(f"**{h}**")

    st.markdown(
        "<hr style='border:none;border-top:1px solid #1e293b;margin:4px 0'>",
        unsafe_allow_html=True,
    )

    for mon in monitors:
        monitor_id   = mon["monitor_id"]
        company_name = mon["company_name"]
        is_active    = bool(mon["is_active"])
        frequency    = mon.get("frequency", "weekly")
        last_run     = mon.get("last_run_at", "")
        total_runs   = mon.get("total_runs", 0)
        total_changes = mon.get("total_changes_found", 0)

        # Next run from APScheduler
        job_status = scheduler.get_job_status(monitor_id)
        next_run   = ""
        if job_status.get("next_run"):
            try:
                dt       = datetime.fromisoformat(job_status["next_run"])
                next_run = dt.strftime("%b %d %H:%M")
            except Exception:
                next_run = job_status["next_run"][:16]

        # Last run display
        last_run_display = "Never"
        if last_run:
            try:
                dt = datetime.fromisoformat(last_run)
                last_run_display = dt.strftime("%b %d %H:%M")
            except Exception:
                last_run_display = last_run[:16]

        row = st.columns([2.5, 1.2, 1.0, 1.5, 1.5, 2.0])

        with row[0]:
            status_icon = "🟢" if is_active else "⚫"
            changes_badge = f" · {total_changes} changes" if total_changes > 0 else ""
            st.markdown(
                f"**{status_icon} {company_name}**{changes_badge}  \n"
                f"<span style='color:#64748b;font-size:0.75rem'>"
                f"{mon.get('company_url', '')[:40]}</span>",
                unsafe_allow_html=True,
            )

        with row[1]:
            st.markdown(
                f"<span style='color:#94a3b8'>{FREQUENCY_LABELS.get(frequency, frequency)}</span>",
                unsafe_allow_html=True,
            )

        with row[2]:
            if is_active and next_run:
                st.markdown(
                    f"<span style='color:#22c55e;font-size:0.8rem'>Next: {next_run}</span>",
                    unsafe_allow_html=True,
                )
            elif is_active:
                st.markdown(
                    "<span style='color:#22c55e;font-size:0.8rem'>Active</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<span style='color:#64748b;font-size:0.8rem'>Paused</span>",
                    unsafe_allow_html=True,
                )

        with row[3]:
            st.markdown(
                f"<span style='color:#94a3b8;font-size:0.8rem'>{last_run_display}</span>",
                unsafe_allow_html=True,
            )

        with row[4]:
            st.markdown(
                f"<span style='color:#94a3b8'>{total_runs} runs</span>",
                unsafe_allow_html=True,
            )

        with row[5]:
            btn1, btn2, btn3, btn4 = st.columns(4)

            with btn1:
                # Run now
                if st.button("▶", key=f"run_{monitor_id}",
                             help="Run immediately", use_container_width=True):
                    success = scheduler.run_now(monitor_id)
                    if success:
                        st.success(f"▶ Running {company_name} now (background)...")
                    else:
                        st.error("Failed to trigger run.")

            with btn2:
                # Toggle active
                toggle_label = "⏸" if is_active else "▶"
                toggle_help  = "Pause" if is_active else "Resume"
                if st.button(toggle_label, key=f"tog_{monitor_id}",
                             help=toggle_help, use_container_width=True):
                    scheduler.toggle_monitor(monitor_id, not is_active)
                    st.rerun()

            with btn3:
                # View events
                if st.button("📋", key=f"ev_{monitor_id}",
                             help="View change events", use_container_width=True):
                    st.session_state["events_monitor_id"] = monitor_id
                    st.session_state["events_company"]    = company_name
                    st.rerun()

            with btn4:
                # Delete
                if st.button("🗑️", key=f"del_{monitor_id}",
                             help="Delete monitor", use_container_width=True):
                    st.session_state[f"confirm_del_{monitor_id}"] = True

        # Confirm delete
        if st.session_state.get(f"confirm_del_{monitor_id}"):
            st.warning(f"Delete monitor for **{company_name}**?")
            yc, nc = st.columns(2)
            with yc:
                if st.button("Yes, delete", key=f"yd_{monitor_id}"):
                    scheduler.remove_monitor(monitor_id)
                    st.session_state.pop(f"confirm_del_{monitor_id}", None)
                    st.success(f"Deleted monitor for {company_name}.")
                    st.rerun()
            with nc:
                if st.button("Cancel", key=f"nd_{monitor_id}"):
                    st.session_state.pop(f"confirm_del_{monitor_id}", None)
                    st.rerun()

        st.markdown(
            "<hr style='border:none;border-top:1px solid #1e293b;margin:2px 0'>",
            unsafe_allow_html=True,
        )

# ── Change events panel ───────────────────────────────────────────────────────
events_monitor_id = st.session_state.get("events_monitor_id")
events_company    = st.session_state.get("events_company", "")

if events_monitor_id:
    st.markdown("---")
    st.markdown(f"### 📊 Change Events — {events_company}")

    if st.button("✕ Close Events Panel"):
        st.session_state.pop("events_monitor_id", None)
        st.session_state.pop("events_company", None)
        st.rerun()

    sev_filter = st.radio(
        "Filter by severity",
        ["All", "High", "Medium", "Low"],
        horizontal=True,
    )
    sev_arg = None if sev_filter == "All" else sev_filter.lower()

    events = list_change_events(
        monitor_id=events_monitor_id,
        limit=50,
        severity=sev_arg,
    )

    if not events:
        st.info(
            "No change events recorded yet. "
            "Events appear after the first scheduled comparison run."
        )
    else:
        for ev in events:
            severity = ev.get("severity", "low")
            css_class = f"event-row-{severity}"
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")

            detected = ev.get("detected_at", "")
            try:
                detected = datetime.fromisoformat(detected).strftime("%b %d %H:%M")
            except Exception:
                pass

            st.markdown(
                f"<div class='{css_class}'>"
                f"<span style='font-weight:700;color:#e2e8f0'>"
                f"{emoji} {ev.get('change_type','').replace('_',' ').title()}"
                f"</span>"
                f"<span style='color:#64748b;font-size:0.75rem;margin-left:8px'>"
                f"{detected}</span><br/>"
                f"<span style='color:#94a3b8;font-size:0.85rem'>"
                f"{ev.get('description','')}</span><br/>"
                f"<span style='color:#64748b;font-size:0.75rem'>"
                f"Before: <code>{ev.get('old_value','')[:50]}</code> → "
                f"Now: <code>{ev.get('new_value','')[:50]}</code>"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("ℹ️ How Monitoring Works"):
    st.markdown("""
**Monitoring Pipeline (per scheduled run):**

1. **APScheduler** triggers the job at the configured frequency
2. The full 7-agent due diligence pipeline runs on the company URL
3. The new run is compared to the previous run using 2-layer change detection:
   - **Structural diff** — fast comparison of funding, risk scores, team, sentiment
   - **LLM semantic analysis** — deeper review of report narrative shifts
4. Change events are classified by severity: 🔴 High / 🟡 Medium / 🟢 Low
5. If significant changes exist, alerts are sent to your configured channels
6. All change events are stored in the database for this history view

**Severity Thresholds:**
- 🔴 **High:** New funding round, leadership change, risk score shift ≥ 3pts
- 🟡 **Medium:** Market position change, sentiment shift, revenue change
- 🟢 **Low:** Tech stack update, minor press coverage, social growth

**Alert Channels:**
- **Email** — Requires Gmail App Password (not your main Gmail password)
- **Slack** — Requires an Incoming Webhook URL from api.slack.com/apps
    """)