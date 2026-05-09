"""
monitoring/alerting.py — Email and Slack alert delivery.

Channels:
  Email — Gmail SMTP via Python's built-in smtplib (no external library)
  Slack — Incoming webhook via requests.post (Block Kit message format)

Both channels fail independently — an error in one never blocks the other.

Usage:
    from monitoring.alerting import send_alerts
    send_alerts(company_name, company_url, events, email="x@y.com", slack_webhook="https://...")
"""

import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import requests

import config
from monitoring.change_detector import ChangeEvent

# ── Formatting helpers ────────────────────────────────────────────────────────

def _severity_color_html(severity: str) -> str:
    return {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}.get(severity, "#94a3b8")

def _build_email_html(company_name: str, company_url: str, events: list[ChangeEvent], run_date: str) -> str:
    high = [e for e in events if e.severity == "high"]
    medium = [e for e in events if e.severity == "medium"]
    low = [e for e in events if e.severity == "low"]

    def event_rows(evts: list[ChangeEvent]) -> str:
        rows = ""
        for e in evts:
            color = _severity_color_html(e.severity)
            rows += f"""
                <tr>
                  <td style="border-bottom: 1px solid #1e293b; padding: 10px;">
                    <span style="color:{color}; font-weight:700">
                        {e.emoji} {e.change_type.replace('_', ' ').title()}
                    </span><br />
                    <span style="color:#94a3b8;font-size:12px">{e.description}</span>
                  </td>
                  <td style="border-bottom: 1px solid #1e293b; padding: 10px; color:#64748b; font-size:12px">
                    {e.old_value}
                  </td>
                  <td style="border-bottom: 1px solid #1e293b; padding: 10px; color:#e2e8f0; font-size:12px">
                    {e.new_value}
                  </td>
                </tr>"""
        return rows

    all_rows = event_rows(high) + event_rows(medium) + event_rows(low)

    return f"""
<!DOCTYPE html>
<html>
<body style="background:#0f172a;font-family:Arial,sans-serif;margin:0;padding:20px;">
  <div style="max-width:600px;margin:0 auto;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#0f172a,#1e3a5f);
                border:1px solid #1d63db;border-radius:12px;padding:24px;
                margin-bottom:20px;">
      <div style="font-size:22px;font-weight:800;color:#e2e8f0;">
        🔔 IntelliDD Pro — Company Change Alert
      </div>
      <div style="color:#94a3b8;margin-top:6px;">
        {company_name} · {run_date}
      </div>
    </div>

    <!-- Summary badges -->
    <div style="margin-bottom:20px;">
      <span style="background:#ef4444;color:white;padding:4px 12px;
                   border-radius:12px;font-size:12px;margin-right:8px;">
        🔴 {len(high)} High
      </span>
      <span style="background:#f59e0b;color:white;padding:4px 12px;
                   border-radius:12px;font-size:12px;margin-right:8px;">
        🟡 {len(medium)} Medium
      </span>
      <span style="background:#22c55e;color:white;padding:4px 12px;
                   border-radius:12px;font-size:12px;">
        🟢 {len(low)} Low
      </span>
    </div>

    <!-- Changes table -->
    <div style="background:#1e293b;border-radius:10px;overflow:hidden;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <thead>
          <tr style="background:#0f2d5c;">
            <th style="padding:12px;text-align:left;color:#60a5fa;font-size:12px;">
              CHANGE
            </th>
            <th style="padding:12px;text-align:left;color:#60a5fa;font-size:12px;">
              PREVIOUS
            </th>
            <th style="padding:12px;text-align:left;color:#60a5fa;font-size:12px;">
              NOW
            </th>
          </tr>
        </thead>
        <tbody style="color:#e2e8f0;">
          {all_rows}
        </tbody>
      </table>
    </div>

    <!-- Footer -->
    <div style="margin-top:20px;color:#64748b;font-size:11px;text-align:center;">
      IntelliDD Pro · Automated Company Intelligence ·
      <a href="{company_url}" style="color:#60a5fa;">{company_url}</a>
    </div>

  </div>
</body>
</html>"""


def _build_slack_blocks(company_name: str, company_url: str, events: list[ChangeEvent], run_date: str) -> dict:
    """Build slack Block kit message payload."""
    high = [e for e in events if e.severity == "high"]
    medium = [e for e in events if e.severity == "medium"]
    low = [e for e in events if e.severity == "low"]

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🔔 {company_name} — Company Change Alert",
            },
        },
        {
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"*IntelliDD Pro* · {run_date} · <{company_url}|{company_url}>",
            }],
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*🔴 High Priority:* {len(high)}"},
                {"type": "mrkdwn", "text": f"*🟡 Medium:* {len(medium)}"},
                {"type": "mrkdwn", "text": f"*🟢 Low:* {len(low)}"},
                {"type": "mrkdwn", "text": f"*Total Changes:* {len(events)}"},
            ],
        },
        {"type": "divider"},
    ]

    # Add top 5 changes as blocks
    for event in events[:5]:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"{event.emoji} *{event.change_type.replace('_', ' ').title()}*\n"
                    f"_{event.description}_\n"
                    f"*Before:* `{event.old_value[:60]}`\n"
                    f"*After:* `{event.new_value[:60]}`",
                ),
            },
        })

    if len(events) > 5:
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": f"And {len(events) - 5} more changes. Check IntelliDD Pro for full details._",
            }],
        })

    return {"blocks": blocks}

# ── Email sender ──────────────────────────────────────────────────────────────

def send_email_alert(to_email: str, company_name: str, company_url: str, events: list[ChangeEvent]) -> bool:
    """
    Send an HTML email alert via Gmail SMTP.

    Requires in .env:
        ALERT_EMAIL_FROM=your_gmail@gmail.com
        ALERT_EMAIL_PASSWORD=your_app_password  (Gmail App Password, not main password)

    Returns True on success, False on failure.
    """
    from_email = config.ALERT_EMAIL_FROM
    password = config.ALERT_EMAIL_PASSWORD

    if not from_email or not password:
        print("  ⚠️  [Alerting] Email not configured — skipping")
        return False
    
    run_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    high_count = sum(1 for e in events if e.severity == "high")

    subject = (
        f"🔴 {company_name} {high_count} High-Priority Changes Detected"
        if high_count > 0
        else f"🟡 {company_name} {len(events)} Changes Detected"
    )

    try:
        msg = MIMEMultipart('alternative')
        msg["Subject"] = subject
        msg["From"] = f"IntelliDD Pro <{from_email}>"
        msg["To"] = to_email

        html_body = _build_email_html(company_name, company_url, events, run_date)
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())

        print(f"  ✅  [Alerting] Email sent to {to_email}")
        return True
    
    except Exception as e:
        print(f"  ❌  [Alerting] Failed to send email: {e}")
        return False


# ── Slack sender ──────────────────────────────────────────────────────────────

def send_slack_alert(webhook_url: str, company_name: str, company_url: str, events: list[ChangeEvent]) -> bool:
    """
    Send a Slack alert via Incoming Webhook (Block Kit format).

    Requires in .env:
        ALERT_SLACK_WEBHOOK=https://hooks.slack.com/services/xxx/yyy/zzz

    Returns True on success, False on failure.
    """
    if not webhook_url:
        print("  ⚠️  [Alerting] Slack webhook not configured — skipping")
        return False

    run_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    payload = _build_slack_blocks(company_name, company_url, events, run_date)

    try:
        response = requests.post(
            webhook_url,
            data = json.dumps(payload),
            timeout=10,
        )
        if response.status_code == 200:
            print(f"  ✅  [Alerting] Slack message sent")
            return True
        else :
            print(f"  ❌  [Alerting] Slack webhook returned {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"  ❌  [Alerting] Failed to send Slack message: {e}")
        return False
    

# ── Unified alert dispatcher ──────────────────────────────────────────────────

def send_alerts(company_name: str, company_url: str, events: list[ChangeEvent], alert_email: Optional[str]=None, alert_slack: Optional[str]=None) -> dict:
    """
    Send alerts to all configured channels.
    Channels fail independently — one failure never blocks another.

    Args:
        company_name:  Display name of the company
        company_url:   Company website URL
        events:        List of ChangeEvent objects
        alert_email:   Optional recipient email address
        alert_slack:   Optional Slack incoming webhook URL

    Returns:
        Dict: {email_sent: bool, slack_sent: bool}
    """

    if not events:
        print("  ℹ️  [Alerting] No events to alert on")
        return {"email_sent": False, "slack_sent": False}
    
    email_sent = False
    slack_sent = False

    if alert_email:
        email_sent = send_email_alert(alert_email, company_name, company_url, events)

    if alert_slack:
        slack_sent = send_slack_alert(alert_slack, company_name, company_url, events)

    if not alert_email and not alert_slack:
        print("  ℹ️  [Alerting] No alert channels configured")

    return {"email_sent": email_sent, "slack_sent": slack_sent}