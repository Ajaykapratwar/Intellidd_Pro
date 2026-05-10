"""
utils/pdf_exporter.py — Report PDF and HTML export.

Pipeline:
  Markdown report  →  styled HTML  →  PDF (via WeasyPrint)
                                   ↘  HTML fallback (if WeasyPrint unavailable)

WeasyPrint on Windows requires GTK libraries.
If WeasyPrint is not available, we return the styled HTML instead.
The HTML is print-ready and can be File → Print → Save as PDF in any browser.

Usage:
    from utils.pdf_exporter import export_report
    result = export_report(report_markdown, company_name, output_dir, risk_scorecard)
    print(result["pdf_path"])    # path to PDF (or HTML if PDF failed)
    print(result["html_path"])   # path to styled HTML always available
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Report CSS ────────────────────────────────────────────────────────────────

REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 10.5pt;
    line-height: 1.65;
    color: #1e293b;
    background: #ffffff;
    max-width: 800px;
    margin: 0 auto;
    padding: 0;
}

/* Cover page */
.cover-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: linear-gradient(160deg, #0f172a 0%, #1e3a5f 60%, #0f2d5c 100%);
    color: white;
    padding: 60px 50px;
    page-break-after: always;
}
.cover-brand {
    font-size: 11pt;
    font-weight: 700;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #60a5fa;
    margin-bottom: 48px;
}
.cover-title {
    font-size: 36pt;
    font-weight: 800;
    line-height: 1.1;
    color: #f1f5f9;
    margin-bottom: 12px;
    letter-spacing: -0.5px;
}
.cover-subtitle {
    font-size: 14pt;
    color: #94a3b8;
    margin-bottom: 48px;
    font-weight: 300;
}
.cover-divider {
    width: 60px;
    height: 3px;
    background: #1d63db;
    margin-bottom: 40px;
}
.cover-meta table { width: 100%; border-collapse: collapse; }
.cover-meta td {
    padding: 8px 0;
    font-size: 9.5pt;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.cover-meta td:first-child { color: #64748b; width: 160px; }
.cover-meta td:last-child  { color: #e2e8f0; font-weight: 500; }
.cover-footer {
    margin-top: auto;
    padding-top: 40px;
    font-size: 8pt;
    color: #334155;
}

/* Risk badge on cover */
.risk-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-right: 8px;
    margin-top: 8px;
}
.risk-low    { background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid #22c55e; }
.risk-medium { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid #f59e0b; }
.risk-high   { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid #ef4444; }

/* Content pages */
.content {
    padding: 50px 50px 60px 50px;
}

/* Page header on content pages */
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 2px solid #1d63db;
    margin-bottom: 32px;
}
.page-header-brand {
    font-size: 8.5pt;
    font-weight: 700;
    color: #1d63db;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.page-header-company {
    font-size: 8.5pt;
    color: #64748b;
}

/* Headings */
h1 {
    font-size: 20pt;
    font-weight: 800;
    color: #0f172a;
    margin: 36px 0 16px 0;
    letter-spacing: -0.3px;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
}
h2 {
    font-size: 13pt;
    font-weight: 700;
    color: #1e293b;
    margin: 28px 0 12px 0;
    padding-left: 10px;
    border-left: 3px solid #1d63db;
}
h3 {
    font-size: 11pt;
    font-weight: 600;
    color: #334155;
    margin: 20px 0 8px 0;
}

/* Paragraphs */
p { margin: 0 0 12px 0; color: #334155; }

/* Lists */
ul, ol { margin: 8px 0 12px 24px; }
li { margin-bottom: 5px; color: #334155; }

/* Emphasis */
strong { font-weight: 700; color: #1e293b; }
em     { font-style: italic; color: #475569; }

/* Code blocks */
code {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    padding: 2px 5px;
    border-radius: 3px;
    color: #0f172a;
}
pre {
    background: #0f172a;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 12px 0;
    font-size: 8.5pt;
    line-height: 1.5;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 9.5pt;
}
thead tr { background: #0f172a; }
thead th {
    padding: 10px 12px;
    text-align: left;
    color: #60a5fa;
    font-weight: 600;
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
tbody tr:nth-child(even) { background: #f8fafc; }
tbody tr:nth-child(odd)  { background: #ffffff; }
tbody td {
    padding: 9px 12px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
    vertical-align: top;
}

/* Risk scorecard section */
.risk-scorecard {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 20px 24px;
    margin: 20px 0;
}
.risk-scorecard-title {
    font-size: 11pt;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 16px;
}
.risk-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #e2e8f0;
}
.risk-row:last-child { border-bottom: none; }
.risk-dim-name  { font-size: 9.5pt; color: #334155; font-weight: 500; }
.risk-dim-score { font-size: 10pt; font-weight: 700; min-width: 60px; text-align: right; }

/* Callout boxes */
.callout {
    border-left: 4px solid #1d63db;
    background: #eff6ff;
    padding: 12px 16px;
    margin: 16px 0;
    border-radius: 0 6px 6px 0;
    font-size: 9.5pt;
    color: #1e3a5f;
}
.callout-warning { border-left-color: #f59e0b; background: #fffbeb; color: #713f12; }
.callout-danger  { border-left-color: #ef4444; background: #fef2f2; color: #7f1d1d; }

/* Footer */
.report-footer {
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid #e2e8f0;
    font-size: 8pt;
    color: #94a3b8;
    text-align: center;
}

/* Print / PDF settings */
@media print {
    body { max-width: 100%; }
    .cover-page { min-height: 100vh; page-break-after: always; }
    h1 { page-break-before: auto; }
    h2 { page-break-after: avoid; }
    table { page-break-inside: avoid; }
    .callout { page-break-inside: avoid; }
}
@page {
    margin: 0;
    size: A4;
}
@page :not(:first) {
    margin: 20mm 20mm 25mm 20mm;
}
"""


# ── Cover page builder ────────────────────────────────────────────────────────

def _build_cover_html(
    company_name:   str,
    company_url:    str,
    sector_label:   str,
    run_date:       str,
    risk_scorecard: dict,
    run_id:         str,
) -> str:
    """Build the cover page HTML."""
    overall_risk  = risk_scorecard.get("overall_risk_score", "N/A")
    confidence    = risk_scorecard.get("dd_confidence_score", "N/A")
    risk_summary  = risk_scorecard.get("risk_summary", "")[:200]

    # Risk badge class
    try:
        r = int(overall_risk)
        badge_class = "risk-low" if r <= 3 else "risk-medium" if r <= 6 else "risk-high"
        badge_label = "Low Risk" if r <= 3 else "Medium Risk" if r <= 6 else "High Risk"
    except (TypeError, ValueError):
        badge_class = "risk-medium"
        badge_label = "Risk N/A"

    return f"""
    <div class="cover-page">
        <div class="cover-brand">IntelliDD Pro · Due Diligence Report</div>

        <div class="cover-title">{company_name}</div>
        <div class="cover-subtitle">{sector_label}</div>

        <div class="cover-divider"></div>

        <div style="margin-bottom: 32px;">
            <span class="risk-badge {badge_class}">{badge_label} · {overall_risk}/10</span>
            <span class="risk-badge" style="background:rgba(29,99,219,0.15);
                  color:#1d63db;border:1px solid #1d63db;">
                DD Confidence {confidence}/100
            </span>
        </div>

        {f'<div style="color:#94a3b8;font-size:9.5pt;margin-bottom:32px;max-width:480px;line-height:1.6">{risk_summary}</div>' if risk_summary else ''}

        <div class="cover-meta">
            <table>
                <tr><td>Company</td><td>{company_name}</td></tr>
                <tr><td>Website</td><td>{company_url}</td></tr>
                <tr><td>Sector</td><td>{sector_label}</td></tr>
                <tr><td>Report Date</td><td>{run_date}</td></tr>
                <tr><td>Report ID</td><td>{run_id}</td></tr>
                <tr><td>Generated By</td><td>IntelliDD Pro · Multi-Agent DD Platform</td></tr>
            </table>
        </div>

        <div class="cover-footer">
            This report was generated automatically by IntelliDD Pro using AI-powered
            multi-agent research. It is intended for informational purposes only and
            does not constitute financial or legal advice. All data sourced from
            publicly available information.
        </div>
    </div>
    """


# ── Risk scorecard HTML ───────────────────────────────────────────────────────

def _build_risk_scorecard_html(risk_scorecard: dict) -> str:
    """Build an inline risk scorecard HTML block for the report."""
    if not risk_scorecard or "error" in risk_scorecard:
        return ""

    dims = [
        ("Founder Risk",      "founder_risk"),
        ("Market Risk",       "market_risk"),
        ("Financial Risk",    "financial_risk"),
        ("Technical Risk",    "technical_risk"),
        ("Reputational Risk", "reputational_risk"),
    ]

    rows = ""
    for label, key in dims:
        dim   = risk_scorecard.get(key, {})
        score = dim.get("score", "N/A")
        sev   = dim.get("severity", "")
        try:
            s = int(score)
            color = "#22c55e" if s <= 3 else "#f59e0b" if s <= 6 else "#ef4444"
        except (TypeError, ValueError):
            color = "#94a3b8"
        rows += f"""
        <div class="risk-row">
            <span class="risk-dim-name">{label} <span style="color:#94a3b8;font-size:8.5pt">({sev})</span></span>
            <span class="risk-dim-score" style="color:{color}">{score}/10</span>
        </div>"""

    overall    = risk_scorecard.get("overall_risk_score", "N/A")
    confidence = risk_scorecard.get("dd_confidence_score", "N/A")

    return f"""
    <div class="risk-scorecard">
        <div class="risk-scorecard-title">📊 Quantitative Risk Scorecard</div>
        {rows}
        <div class="risk-row" style="margin-top:8px;padding-top:12px;border-top:2px solid #e2e8f0;border-bottom:none;">
            <span class="risk-dim-name"><strong>Overall Risk Score</strong></span>
            <span class="risk-dim-score" style="font-size:13pt;color:#1d63db"><strong>{overall}/10</strong></span>
        </div>
        <div class="risk-row" style="border-bottom:none;">
            <span class="risk-dim-name" style="color:#94a3b8">DD Confidence Score</span>
            <span class="risk-dim-score" style="color:#64748b">{confidence}/100</span>
        </div>
    </div>
    """


# ── Markdown → HTML converter ─────────────────────────────────────────────────

def _markdown_to_html(md_text: str) -> str:
    """Convert Markdown to HTML using the markdown library."""
    try:
        import markdown
        return markdown.markdown(
            md_text,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )
    except ImportError:
        # Fallback: very basic regex-based conversion
        html = md_text
        # Headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$',  r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$',   r'<h1>\1</h1>', html, flags=re.MULTILINE)
        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*',     r'<em>\1</em>', html)
        # Paragraphs
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'
        return html


# ── Full HTML report builder ──────────────────────────────────────────────────

def build_report_html(
    report_markdown: str,
    company_name:    str,
    company_url:     str,
    sector_label:    str,
    risk_scorecard:  dict,
    run_id:          str,
    run_date:        Optional[str] = None,
) -> str:
    """
    Build a complete, standalone HTML report document.

    Args:
        report_markdown:  The full report markdown string
        company_name:     Company display name
        company_url:      Company URL
        sector_label:     Detected sector label
        risk_scorecard:   Risk scorecard dict from risk_scorer agent
        run_id:           Pipeline run ID
        run_date:         Optional date string (defaults to today)

    Returns:
        Complete HTML string ready to save or convert to PDF.
    """
    if not run_date:
        run_date = datetime.now().strftime("%B %d, %Y")

    cover_html     = _build_cover_html(
        company_name, company_url, sector_label,
        run_date, risk_scorecard, run_id
    )
    risk_html      = _build_risk_scorecard_html(risk_scorecard)
    content_html   = _markdown_to_html(report_markdown)

    # Inject risk scorecard after executive summary if present
    if risk_html and "<h2" in content_html:
        # Insert after the first h2 section
        insert_after = content_html.find("</h2>") + len("</h2>")
        # Find the next h2 to insert before it
        next_h2 = content_html.find("<h2", insert_after)
        if next_h2 > 0:
            content_html = (
                content_html[:next_h2] +
                risk_html +
                content_html[next_h2:]
            )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Due Diligence Report — {company_name}</title>
    <style>{REPORT_CSS}</style>
</head>
<body>

    {cover_html}

    <div class="content">
        <div class="page-header">
            <span class="page-header-brand">IntelliDD Pro · Due Diligence</span>
            <span class="page-header-company">{company_name} · {run_date}</span>
        </div>

        {content_html}

        <div class="report-footer">
            Generated by IntelliDD Pro · Run ID: {run_id} · {run_date}<br/>
            This report is AI-generated from publicly available sources.
            Not financial or legal advice.
        </div>
    </div>

</body>
</html>"""


# ── Export functions ──────────────────────────────────────────────────────────

def export_to_html(
    html_content: str,
    output_path:  str,
) -> str:
    """Save HTML content to disk. Always succeeds."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_content, encoding="utf-8")
    print(f"  ✅ [PDF Exporter] HTML saved: {path}")
    return str(path)


def export_to_pdf(
    html_content: str,
    output_path:  str,
) -> Optional[str]:
    """
    Convert HTML to PDF using WeasyPrint.

    Returns the PDF path on success, None if WeasyPrint is unavailable.

    WeasyPrint on Windows requires GTK3 runtime.
    Download from: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
    Alternatively, open the HTML file in a browser and use File → Print → Save as PDF.
    """
    try:
        from weasyprint import HTML as WeasyHTML
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        WeasyHTML(string=html_content).write_pdf(str(path))
        print(f"  ✅ [PDF Exporter] PDF saved: {path}")
        return str(path)
    except ImportError:
        print("  ⚠️  [PDF Exporter] WeasyPrint not installed")
        return None
    except Exception as e:
        print(f"  ⚠️  [PDF Exporter] WeasyPrint failed: {e}")
        print("       On Windows: install GTK3 from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer")
        print("       Alternative: open the HTML in a browser → File → Print → Save as PDF")
        return None


def export_report(
    report_markdown: str,
    company_name:    str,
    company_url:     str,
    sector_label:    str,
    risk_scorecard:  dict,
    run_id:          str,
    output_dir:      str,
    run_date:        Optional[str] = None,
) -> dict:
    """
    Main export entry point — generates both HTML and PDF (if possible).

    Args:
        report_markdown: Full report markdown string
        company_name:    Company display name
        company_url:     Company URL
        sector_label:    Sector label string
        risk_scorecard:  Risk scorecard dict
        run_id:          Pipeline run ID
        output_dir:      Directory to save files
        run_date:        Optional date string

    Returns:
        Dict with:
            html_path  — always present (styled HTML)
            pdf_path   — PDF path if WeasyPrint succeeded, else None
            html_bytes — HTML file bytes for Streamlit download button
            pdf_bytes  — PDF file bytes for Streamlit download button (or None)
    """
    if not run_date:
        run_date = datetime.now().strftime("%B %d, %Y")

    company_slug = (
        company_url.replace("https://", "").replace("http://", "")
        .replace("www.", "").split("/")[0].split(".")[0].lower()
    )

    # Build HTML
    html_content = build_report_html(
        report_markdown=report_markdown,
        company_name=company_name,
        company_url=company_url,
        sector_label=sector_label,
        risk_scorecard=risk_scorecard,
        run_id=run_id,
        run_date=run_date,
    )

    # Save HTML (always works)
    html_path = str(Path(output_dir) / f"{company_slug}_report.html")
    export_to_html(html_content, html_path)

    # Try PDF
    pdf_path = str(Path(output_dir) / f"{company_slug}_report.pdf")
    pdf_result = export_to_pdf(html_content, pdf_path)

    # Read bytes for Streamlit download buttons
    html_bytes = html_content.encode("utf-8")
    pdf_bytes  = None

    if pdf_result:
        try:
            pdf_bytes = Path(pdf_result).read_bytes()
        except Exception:
            pass

    return {
        "html_path":  html_path,
        "pdf_path":   pdf_result,
        "html_bytes": html_bytes,
        "pdf_bytes":  pdf_bytes,
    }


if __name__ == "__main__":
    # Quick test — run: uv run python utils/pdf_exporter.py
    print("Testing PDF exporter...\n")

    sample_md = """# Due Diligence Report: Test Company
*Report generated by IntelliDD Pro | May 08, 2026*

## Executive Summary
Test company is a leading provider of AI solutions with $400M in funding.

## Team & Leadership
Founded by Jane Doe (CEO) and John Smith (CTO), both formerly of Google.

## Risk Assessment
1. **Market Risk** — Medium: competitive landscape
2. **Financial Risk** — Low: strong revenue growth
    """

    sample_risk = {
        "founder_risk":      {"score": 3, "severity": "Low"},
        "market_risk":       {"score": 5, "severity": "Medium"},
        "financial_risk":    {"score": 4, "severity": "Medium"},
        "technical_risk":    {"score": 2, "severity": "Low"},
        "reputational_risk": {"score": 3, "severity": "Low"},
        "overall_risk_score": 3,
        "dd_confidence_score": 78,
        "risk_summary": "Overall the company shows strong fundamentals.",
    }

    result = export_report(
        report_markdown=sample_md,
        company_name="Test Company",
        company_url="https://testcompany.com",
        sector_label="AI / Developer Tools",
        risk_scorecard=sample_risk,
        run_id="test001",
        output_dir="./outputs/test_export",
    )

    print(f"HTML: {result['html_path']}")
    print(f"PDF:  {result['pdf_path'] or 'Not available (WeasyPrint not installed)'}")
    print(f"HTML size: {len(result['html_bytes']):,} bytes")