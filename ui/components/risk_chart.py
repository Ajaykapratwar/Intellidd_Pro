"""
ui/components/risk_chart.py — Plotly risk visualizations.

Generates two charts from a risk_scorecard dict:
  1. radar_chart()  — 5-dimension risk radar
  2. gauge_chart()  — DD Confidence Score gauge

Usage in Streamlit:
    from ui.components.risk_chart import radar_chart, gauge_chart
    st.plotly_chart(radar_chart(risk_scorecard), use_container_width=True)
    st.plotly_chart(gauge_chart(risk_scorecard), use_container_width=True)
"""

import plotly.graph_objects as go
import plotly.express as px
from typing import Optional


# ── Colour palette ────────────────────────────────────────────────────────────
COLORS = {
    "low":      "#22c55e",   # green
    "medium":   "#f59e0b",   # amber
    "high":     "#ef4444",   # red
    "critical": "#7c3aed",   # purple
    "fill":     "rgba(29, 99, 219, 0.25)",   # semi-transparent blue
    "line":     "#1d63db",   # solid blue
    "bg":       "#0f172a",   # dark background
    "grid":     "#1e293b",   # grid lines
    "text":     "#e2e8f0",   # light text
}

DIMENSION_LABELS = [
    "Founder Risk",
    "Market Risk",
    "Financial Risk",
    "Technical Risk",
    "Reputational Risk",
]

DIMENSION_KEYS = [
    "founder_risk",
    "market_risk",
    "financial_risk",
    "technical_risk",
    "reputational_risk",
]


def _get_score_color(score: int) -> str:
    """Return color based on risk score."""
    if score <= 3:
        return COLORS["low"]
    elif score <= 6:
        return COLORS["medium"]
    elif score <= 9:
        return COLORS["high"]
    else:
        return COLORS["critical"]


def radar_chart(
    risk_scorecard: dict,
    company_name: str = "Company",
    dark_mode: bool = True,
) -> go.Figure:
    """
    Generate a radar (spider) chart showing all 5 risk dimensions.

    Lower score = lower risk = better (scores are RISK scores, not quality scores).
    The chart inverts this visually — a small polygon = low risk = good.

    Args:
        risk_scorecard: The dict from risk_scorer.py (risk_scorecard.json)
        company_name:   Label for the chart title
        dark_mode:      Use dark background (True for Streamlit dark theme)

    Returns:
        Plotly Figure object — pass directly to st.plotly_chart()
    """
    # Extract scores for each dimension
    scores = []
    hover_texts = []

    for key, label in zip(DIMENSION_KEYS, DIMENSION_LABELS):
        dim_data = risk_scorecard.get(key, {})
        score = dim_data.get("score", 5)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 5

        severity = dim_data.get("severity", "Medium")
        evidence = dim_data.get("evidence", "No data")

        scores.append(score)
        hover_texts.append(
            f"<b>{label}</b><br>"
            f"Score: {score}/10<br>"
            f"Severity: {severity}<br>"
            f"<i>{evidence[:80]}...</i>"
        )

    # Close the polygon by repeating first value
    scores_closed = scores + [scores[0]]
    labels_closed = DIMENSION_LABELS + [DIMENSION_LABELS[0]]
    hover_closed = hover_texts + [hover_texts[0]]

    # Determine overall risk level for fill color
    overall = risk_scorecard.get("overall_risk_score", 5)
    try:
        overall = int(overall)
    except (ValueError, TypeError):
        overall = 5
    fill_color = _get_score_color(overall).replace(")", ", 0.3)").replace("rgb", "rgba") \
        if "rgb" in _get_score_color(overall) else "rgba(29, 99, 219, 0.3)"

    bg_color = COLORS["bg"] if dark_mode else "#ffffff"
    grid_color = COLORS["grid"] if dark_mode else "#e2e8f0"
    text_color = COLORS["text"] if dark_mode else "#1e293b"

    fig = go.Figure()

    # Main risk polygon
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(239, 68, 68, 0.2)",
        line=dict(color="#ef4444", width=2),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_closed,
        name="Risk Profile",
    ))

    # Reference line at score 5 (medium risk boundary)
    reference_scores = [5, 5, 5, 5, 5, 5]
    fig.add_trace(go.Scatterpolar(
        r=reference_scores,
        theta=labels_closed,
        fill=None,
        line=dict(color="rgba(245, 158, 11, 0.5)", width=1, dash="dash"),
        hoverinfo="skip",
        name="Medium Risk (5)",
        showlegend=True,
    ))

    fig.update_layout(
        title=dict(
            text=f"<b>Risk Profile: {company_name}</b>",
            font=dict(size=16, color=text_color),
            x=0.5,
        ),
        polar=dict(
            bgcolor=bg_color,
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickvals=[2, 4, 6, 8, 10],
                ticktext=["2", "4", "6", "8", "10"],
                tickfont=dict(size=10, color=text_color),
                gridcolor=grid_color,
                linecolor=grid_color,
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=text_color),
                gridcolor=grid_color,
                linecolor=grid_color,
            ),
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        font=dict(color=text_color),
        legend=dict(
            font=dict(color=text_color, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=420,
        margin=dict(t=60, b=40, l=60, r=60),
    )

    return fig


def gauge_chart(
    risk_scorecard: dict,
    company_name: str = "Company",
    dark_mode: bool = True,
) -> go.Figure:
    """
    Generate a gauge chart showing the DD Confidence Score (0-100).

    High confidence = we have good data to make a decision.
    Low confidence = data gaps make the assessment uncertain.

    Args:
        risk_scorecard: The dict from risk_scorer.py
        company_name:   Label for the chart
        dark_mode:      Dark background for Streamlit

    Returns:
        Plotly Figure object
    """
    confidence = risk_scorecard.get("dd_confidence_score", 50)
    try:
        confidence = int(confidence)
    except (ValueError, TypeError):
        confidence = 50
    confidence = max(0, min(100, confidence))  # clamp to 0-100

    # Color based on confidence level
    if confidence >= 75:
        bar_color = COLORS["low"]       # green = high confidence
        label = "High Confidence"
    elif confidence >= 50:
        bar_color = COLORS["medium"]    # amber = medium confidence
        label = "Medium Confidence"
    else:
        bar_color = COLORS["high"]      # red = low confidence
        label = "Low Confidence"

    bg_color = COLORS["bg"] if dark_mode else "#ffffff"
    text_color = COLORS["text"] if dark_mode else "#1e293b"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=confidence,
        title=dict(
            text=f"<b>DD Confidence Score</b><br><span style='font-size:0.8em'>{company_name}</span>",
            font=dict(size=15, color=text_color),
        ),
        number=dict(
            suffix="/100",
            font=dict(size=32, color=text_color),
        ),
        delta=dict(
            reference=50,
            increasing=dict(color=COLORS["low"]),
            decreasing=dict(color=COLORS["high"]),
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["0", "25", "50", "75", "100"],
                tickfont=dict(color=text_color, size=11),
            ),
            bar=dict(color=bar_color, thickness=0.7),
            bgcolor=COLORS["grid"],
            borderwidth=0,
            steps=[
                dict(range=[0, 33],  color="rgba(239, 68, 68, 0.15)"),
                dict(range=[33, 66], color="rgba(245, 158, 11, 0.15)"),
                dict(range=[66, 100], color="rgba(34, 197, 94, 0.15)"),
            ],
            threshold=dict(
                line=dict(color=text_color, width=2),
                thickness=0.85,
                value=confidence,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor=bg_color,
        font=dict(color=text_color),
        height=280,
        margin=dict(t=80, b=20, l=40, r=40),
    )

    return fig


def risk_summary_cards(risk_scorecard: dict) -> list[dict]:
    """
    Returns a list of card dicts for rendering in Streamlit columns.

    Each card has: title, score, severity, icon, color, evidence, mitigation

    Usage:
        cards = risk_summary_cards(risk_scorecard)
        cols = st.columns(5)
        for col, card in zip(cols, cards):
            with col:
                st.metric(card['title'], f"{card['score']}/10")
    """
    cards = []
    for key, label in zip(DIMENSION_KEYS, DIMENSION_LABELS):
        dim = risk_scorecard.get(key, {})
        score = dim.get("score", 5)
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 5

        severity = dim.get("severity", "Medium")
        icon = {
            "Low": "✅",
            "Medium": "⚠️",
            "High": "🔴",
            "Critical": "💀",
        }.get(severity, "❓")

        color = {
            "Low":      "#22c55e",
            "Medium":   "#f59e0b",
            "High":     "#ef4444",
            "Critical": "#7c3aed",
        }.get(severity, "#94a3b8")

        cards.append({
            "title":      label,
            "score":      score,
            "severity":   severity,
            "icon":       icon,
            "color":      color,
            "evidence":   dim.get("evidence", ""),
            "mitigation": dim.get("mitigation", ""),
            "key_factors": dim.get("key_factors", []),
        })

    return cards


if __name__ == "__main__":
    # Quick test with dummy data — run: uv run python ui/components/risk_chart.py
    sample_scorecard = {
        "founder_risk":      {"score": 3, "severity": "Low",    "evidence": "Strong technical founders", "mitigation": "None needed"},
        "market_risk":       {"score": 6, "severity": "Medium", "evidence": "Competitive market",        "mitigation": "Focus on differentiation"},
        "financial_risk":    {"score": 4, "severity": "Medium", "evidence": "$400M raised, strong ARR",  "mitigation": "Monitor burn rate"},
        "technical_risk":    {"score": 2, "severity": "Low",    "evidence": "Strong OSS presence",       "mitigation": "None needed"},
        "reputational_risk": {"score": 3, "severity": "Low",    "evidence": "Positive press",            "mitigation": "None needed"},
        "overall_risk_score": 4,
        "dd_confidence_score": 72,
    }

    radar = radar_chart(sample_scorecard, "Test Company")
    gauge = gauge_chart(sample_scorecard, "Test Company")

    radar.show()
    gauge.show()
    print("Charts generated successfully")