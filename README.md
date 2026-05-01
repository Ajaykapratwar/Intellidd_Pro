<div align="center">

<br/>

```
██╗███╗   ██╗████████╗███████╗██╗     ██╗██████╗ ██████╗     ██████╗ ██████╗  ██████╗
██║████╗  ██║╚══██╔══╝██╔════╝██║     ██║██╔══██╗██╔══██╗    ██╔══██╗██╔══██╗██╔═══██╗
██║██╔██╗ ██║   ██║   █████╗  ██║     ██║██║  ██║██║  ██║    ██████╔╝██████╔╝██║   ██║
██║██║╚██╗██║   ██║   ██╔══╝  ██║     ██║██║  ██║██║  ██║    ██╔═══╝ ██╔══██╗██║   ██║
██║██║ ╚████║   ██║   ███████╗███████╗██║██████╔╝██████╔╝    ██║     ██║  ██║╚██████╔╝
╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚══════╝╚═╝╚═════╝ ╚═════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝
```

### AI-Powered Multi-Agent Due Diligence Intelligence Platform

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-Free_Tier-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://console.groq.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangSmith](https://img.shields.io/badge/LangSmith-Tracing-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://smith.langchain.com)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![uv](https://img.shields.io/badge/uv-Package_Manager-DE5FE9?style=for-the-badge)](https://github.com/astral-sh/uv)
[![100% Free Tier](https://img.shields.io/badge/Cost-100%25_Free_Tier-22c55e?style=for-the-badge)](#-free-tier-stack)

<br/>

> **Transform a single company URL into an investment-grade due diligence report in under 4 minutes.**
> 7 specialized AI agents research in parallel, score risk quantitatively, benchmark against competitors,
> and synthesize everything into a structured report — all on free-tier APIs.

<br/>

[**Quick Start**](#-quick-start) · [**Features**](#-features) · [**Architecture**](#-architecture) · [**Tech Stack**](#-free-tier-stack) · [**Roadmap**](#-roadmap)

<br/>

</div>

---

## 📌 What is IntelliDD Pro?

IntelliDD Pro is a **production-grade, multi-agent due diligence system** built on [LangGraph](https://langchain-ai.github.io/langgraph/). Feed it any company URL and it autonomously dispatches 7 specialized AI agents that research the company across every critical investment dimension simultaneously — then synthesizes the findings into a structured, sector-aware report complete with quantitative risk scores and competitor analysis.

This project extends and significantly surpasses the baseline [`awesome-ai-apps/due_diligence_agent`](https://github.com/Arindam200/awesome-ai-apps/tree/main/advance_ai_agents/due_diligence_agent) by:

- **Replacing all paid APIs** with free-tier alternatives (no credit card required for basic use)
- **Adding a 7th Competitor Intelligence Agent** with automatic competitor discovery and positioning matrix
- **Introducing quantitative Risk Scoring** across 5 dimensions with Plotly radar + gauge visualizations
- **Building sector-aware prompts** for 7 industry verticals (AI/Tech, Fintech, Healthcare, SaaS, E-commerce, Consumer, DeepTech)
- **Wiring in LangSmith observability** so every agent trace is inspectable in a dashboard
- **Adding persistent SQLite storage** with run history and report comparison *(Phase 4)*
- **Integrating document RAG** via ChromaDB so uploaded pitch decks augment web research *(Phase 3)*
- **Implementing a ReAct Q&A agent** for interactive post-report questioning *(Phase 5)*

---

## ✨ Features

### 🤖 7 Parallel Specialist Agents

Each agent runs concurrently via `ThreadPoolExecutor`, researching a different dimension of the company:

| Agent | Researches | Output |
|-------|-----------|--------|
| 🌱 **Seed Crawler** | Company homepage, tagline, business model | `company_profile.json` |
| 👥 **Team Agent** | Founders, executives, advisors, hiring signals | `founders_team.json` |
| 💰 **Investor Agent** | Funding rounds, investor quality, runway | `investors.json` |
| 📰 **Press Agent** | Media coverage, sentiment, key narratives | `press.json` |
| 📊 **Financials Agent** | Revenue signals, unit economics, burn rate | `financials.json` |
| ⚙️ **Tech Stack Agent** | Architecture, GitHub presence, security posture | `tech_stack.json` |
| 📱 **Social Agent** | LinkedIn, Twitter/X, community, brand strength | `social.json` |
| 🏆 **Competitor Intel Agent** | 3–5 competitors, comparison matrix, positioning | `competitor_intel.json` |

### 📈 Quantitative Risk Scoring Engine

After all agents complete, a dedicated **Risk Scorer** produces a structured scorecard across 5 investment dimensions:

```
✅ Founder Risk     : 3/10  [Low]
⚠️  Market Risk      : 6/10  [Medium]
⚠️  Financial Risk   : 4/10  [Medium]
✅ Technical Risk   : 2/10  [Low]
✅ Reputational Risk : 3/10  [Low]
──────────────────────────────────
🎯 Overall Risk Score  : 4/10
💡 DD Confidence Score : 72/100
```

Visualized as an interactive **Plotly radar chart** + **gauge chart** in the Streamlit UI.

### 🏷️ Sector-Aware Research (7 Verticals)

Every agent's prompts are dynamically tailored based on the detected industry sector:

| Sector | What Changes |
|--------|-------------|
| **AI / Dev Tools** | Looks for GPU cost margins, inference stack, OSS conversion rate, NeurIPS publications |
| **Fintech** | Looks for TPV, take rate, default rate, PCI DSS, regulatory capital |
| **Healthcare** | Looks for FDA clearance, HIPAA compliance, EHR integration, clinical trial status |
| **B2B SaaS** | Looks for NRR, ACV, Rule of 40, SOC 2, sales cycle length |
| **E-commerce** | Looks for GMV, contribution margin per order, take rate, CAC payback |
| **Consumer** | Looks for DAU/MAU ratio, D30 retention, ARPU, LTV:CAC |
| **Deep Tech** | Looks for TRL level, patent portfolio, CapEx curve, government contracts |

### 🔍 Competitor Intelligence

- Automatically discovers 3–5 direct competitors from a single URL
- Profiles each competitor: funding, stage, employee count, key differentiators
- Produces a **side-by-side comparison matrix** scored across 6 dimensions
- Outputs market position: `Leader / Strong Challenger / Challenger / Niche Player / New Entrant`
- Calculates a **Differentiation Score (0–100)** for the target company

### 📡 LangSmith Observability

Every LLM call and tool invocation is traced via LangSmith:
- Per-agent latency, token count, and input/output
- Full reasoning chain visible in dashboard
- "View Trace" button in UI linking to exact run

### 🆓 100% Free Tier Stack

The entire pipeline runs with zero paid API costs for standard use:

| Component | Tool | Free Limit |
|-----------|------|-----------|
| Primary LLM | Groq (`llama-3.3-70b`) | 14,400 req/day |
| Fallback LLM | Google Gemini 1.5 Flash | 1,500 req/day |
| Web Scraper | Firecrawl | 500 scrapes/month |
| Web Search | DuckDuckGo SDK | No limit (no key needed) |
| Observability | LangSmith | 5,000 traces/month |
| Vector DB | ChromaDB (local) | Unlimited |
| Persistence | SQLite (local) | Unlimited |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                         │
│      [URL Input] [Upload Docs] [History] [Chat] [Alerts]    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              LangGraph Orchestration Layer                    │
│                                                              │
│  ┌───────────┐   ┌──────────────────────────────────────┐   │
│  │   Seed    │   │     Parallel Specialist Agents       │   │
│  │  Crawler  │──▶│  Team │ Investors │ Press │ Finance  │   │
│  │   Agent   │   │  TechStack │ Social │ CompetitorIntel│   │
│  └───────────┘   └──────────────────┬───────────────────┘   │
│                                     │                        │
│  ┌──────────┐   ┌──────────┐       │                        │
│  │   Risk   │   │Validator │◀──────┘                        │
│  │  Scorer  │◀──│  Agent   │                                │
│  └──────────┘   └──────────┘                                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Synthesis Agent  ──▶  Markdown + PDF Report        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   ReAct Q&A Agent (LangGraph subgraph + tools)       │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
┌───────▼──────────┐      ┌──────────▼──────────────────────┐
│  Free Tool Layer  │      │       Persistence Layer         │
│                   │      │                                  │
│  Groq (LLM)       │      │  SQLite    (run history)        │
│  Gemini (fallback)│      │  ChromaDB  (document RAG)       │
│  DuckDuckGo SDK   │      │  APScheduler (monitoring)       │
│  Firecrawl / BS4  │      │  LangSmith  (traces)            │
│  Plotly (charts)  │      │  WeasyPrint (PDF export)        │
└───────────────────┘      └─────────────────────────────────┘
```

### Pipeline Flow

```
START
  │
  ▼
[seed_node]           ← scrape homepage, extract company profile, detect sector
  │
  ▼
[specialists_node]    ← 7 agents run in PARALLEL via ThreadPoolExecutor
  │  ├── TeamAgent
  │  ├── InvestorAgent
  │  ├── PressAgent
  │  ├── FinancialsAgent
  │  ├── TechStackAgent
  │  ├── SocialAgent
  │  └── CompetitorAgent  ← NEW vs baseline
  │
  ▼
[validator_node]      ← cross-checks all outputs, flags contradictions + gaps
  │
  ▼
[risk_node]           ← scores 5 risk dimensions, produces radar + gauge charts
  │
  ▼
[synthesis_node]      ← writes full markdown report + PDF
  │
  ▼
END
```

---

## 📁 Project Structure

```
intellidd_pro/
├── pyproject.toml              # uv project manifest + all dependencies
├── config.py                   # central config — all env vars live here
├── .env.example                # template — copy to .env and fill keys
│
├── agents/                     # one file per specialist agent
│   ├── seed_crawler.py         # stage 1: website crawl + profile extraction
│   ├── team_agent.py           # stage 2a: founders + leadership research
│   ├── investor_agent.py       # stage 2b: funding + investor research
│   ├── press_agent.py          # stage 2c: media coverage + sentiment
│   ├── financials_agent.py     # stage 2d: financial signals extraction
│   ├── tech_stack_agent.py     # stage 2e: technology + engineering research
│   ├── social_agent.py         # stage 2f: social media + brand research
│   ├── competitor_agent.py     # stage 2g: competitor discovery + matrix ⭐
│   ├── validator_agent.py      # stage 3: cross-validation + gap detection
│   ├── risk_scorer.py          # stage 3b: quantitative risk scoring ⭐
│   └── synthesis_agent.py      # stage 4: final report generation
│
├── pipeline/
│   ├── state.py                # DDState TypedDict — shared data contract
│   ├── graph.py                # LangGraph StateGraph wiring
│   └── runner.py               # public entry point: run_due_diligence(url)
│
├── prompts/
│   ├── agent_prompts.py        # all LLM prompts — one place to tune
│   ├── sectors.py              # sector detection enum + detect_sector()
│   └── sector_prompts.py       # sector-specific research signals per agent ⭐
│
├── tools/
│   ├── llm_factory.py          # Groq + Gemini factory with auto-fallback + retry
│   ├── scraper.py              # Firecrawl → Playwright → BS4 degradation stack
│   └── search.py               # DuckDuckGo SDK wrapper (no key needed)
│
├── ui/
│   ├── components/
│   │   ├── risk_chart.py       # Plotly radar + gauge chart components ⭐
│   │   ├── report_card.py      # structured report display (Phase 4)
│   │   └── comparison_diff.py  # run comparison view (Phase 4)
│   └── pages/
│       ├── 1_Research.py       # main DD pipeline page
│       ├── 2_History.py        # past reports + comparison (Phase 4)
│       ├── 3_Monitoring.py     # company monitor management (Phase 7)
│       └── 4_QA_Chat.py        # ReAct Q&A chat interface (Phase 5)
│
├── rag/                        # Phase 3
│   ├── document_processor.py   # PDF/CSV/XLSX → chunks
│   └── vector_store.py         # ChromaDB operations
│
├── persistence/                # Phase 4
│   ├── db.py                   # SQLite setup + migrations
│   └── queries.py              # all query functions
│
├── monitoring/                 # Phase 7
│   ├── scheduler.py            # APScheduler setup
│   ├── change_detector.py      # report diffing logic
│   └── alerting.py             # email + Slack alerts
│
└── outputs/                    # auto-created per run
    └── {company}_{timestamp}_{run_id}/
        ├── company_profile.json
        ├── founders_team.json
        ├── investors.json
        ├── press.json
        ├── financials.json
        ├── tech_stack.json
        ├── social.json
        ├── competitor_intel.json   ⭐
        ├── validation_notes.json
        ├── risk_scorecard.json     ⭐
        ├── report.md
        └── report.pdf              (Phase 4)
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- A free [Groq API key](https://console.groq.com) ← the only required key

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/intellidd-pro.git
cd intellidd-pro

# Create virtual environment and install all dependencies
uv venv
uv sync

# Install Playwright browser (one-time setup)
uv run playwright install chromium
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Open `.env` and add your keys:

```bash
# REQUIRED — free at https://console.groq.com (no credit card)
GROQ_API_KEY=your_groq_key_here

# RECOMMENDED — free at https://aistudio.google.com (LLM fallback)
GOOGLE_API_KEY=your_google_key_here

# OPTIONAL — free at https://firecrawl.dev (better scraping)
FIRECRAWL_API_KEY=your_firecrawl_key_here

# OPTIONAL — free at https://smith.langchain.com (agent observability)
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
```

### 3. Verify Setup

```bash
uv run python config.py
```

You should see:
```
✅ All configuration looks good!
Active LLM:  groq (llama-3.3-70b-versatile)
Firecrawl:   enabled
LangSmith:   enabled
```

### 4. Run Your First Due Diligence

```bash
uv run python pipeline/runner.py https://stripe.com
```

That's it. The pipeline will:
1. Scrape the company website
2. Run 7 agents in parallel
3. Score risk across 5 dimensions
4. Write the full report to `outputs/stripe_YYYYMMDD_HHMMSS/report.md`

---

## 🖥️ Streamlit UI

```bash
uv run streamlit run main.py
```

Open `http://localhost:8501` in your browser.

---

## 📊 Sample Output Structure

After running on any company, the `outputs/` folder contains:

```json
// risk_scorecard.json — example output
{
  "founder_risk": {
    "score": 3,
    "severity": "Low",
    "key_factors": ["Strong technical founders", "Prior exits", "Deep domain expertise"],
    "evidence": "Founders previously at Google Brain and DeepMind...",
    "mitigation": "No action needed — team strength is a positive signal"
  },
  "market_risk": {
    "score": 6,
    "severity": "Medium",
    "key_factors": ["Highly competitive space", "Large incumbents", "Commoditization risk"],
    "evidence": "Market has 8+ funded competitors including OpenAI, Cohere...",
    "mitigation": "Focus on open-source moat and community lock-in"
  },
  "overall_risk_score": 4,
  "dd_confidence_score": 72,
  "risk_summary": "..."
}
```

```json
// competitor_intel.json — example output
{
  "competitors": [
    {
      "name": "OpenAI",
      "funding_total": "$11.3B",
      "overlap_score": 8,
      "strengths_vs_target": ["Larger model capability", "ChatGPT brand recognition"],
      "weaknesses_vs_target": ["Closed source", "Higher pricing", "No community hub"]
    }
  ],
  "market_position": "Strong Challenger",
  "differentiation_score": 78,
  "moat_assessment": "Open-source community flywheel with 1M+ models hosted creates switching cost..."
}
```

---

## 🆚 IntelliDD Pro vs Baseline Project

| Feature | Baseline (`due_diligence_agent`) | **IntelliDD Pro** |
|---------|----------------------------------|-------------------|
| Agent Framework | AG2 / AutoGen | **LangGraph** |
| LLM Provider | Nebius (paid) | **Groq free + Gemini fallback** |
| Web Scraper | TinyFish (paid) | **Firecrawl free / Playwright / BS4** |
| Web Search | Hardcoded URLs | **DuckDuckGo SDK (no key)** |
| Specialist Agents | 6 agents | **7 agents (+Competitor Intel)** |
| Sector Awareness | None (generic prompts) | **7 sector-specific prompt systems** |
| Risk Analysis | None | **5-dimension quantitative scoring** |
| Visualizations | None | **Plotly radar + gauge charts** |
| Document RAG | None | **ChromaDB + sentence-transformers** |
| Persistence | JSON files only | **SQLite + full run history** |
| Observability | None | **LangSmith tracing** |
| Q&A Agent | Prompt only (not wired) | **Full ReAct LangGraph subgraph** |
| Monitoring | None | **APScheduler + email/Slack alerts** |
| PDF Export | None | **WeasyPrint styled PDF** |
| Zero-cost runnable | ❌ (requires paid keys) | **✅ 100% free tier** |

---

## 🆓 Free Tier Stack

| Layer | Tool | Free Tier | Sign Up |
|-------|------|-----------|---------|
| **Primary LLM** | Groq `llama-3.3-70b` | 14,400 req/day | [console.groq.com](https://console.groq.com) |
| **Fallback LLM** | Google Gemini 1.5 Flash | 1,500 req/day | [aistudio.google.com](https://aistudio.google.com) |
| **Web Scraper** | Firecrawl | 500 scrapes/month | [firecrawl.dev](https://firecrawl.dev) |
| **Web Search** | DuckDuckGo SDK | Unlimited | `pip install duckduckgo-search` |
| **Observability** | LangSmith | 5,000 traces/month | [smith.langchain.com](https://smith.langchain.com) |
| **Vector DB** | ChromaDB (local) | Unlimited | Built-in |
| **Persistence** | SQLite (local) | Unlimited | Built-in Python |
| **Scraper fallback** | Playwright + BS4 | Unlimited | Built-in |

**Total monthly cost for standard use: $0**

---

## 🗺️ Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 0** | ✅ Complete | Project setup, uv environment, free tool layer |
| **Phase 1** | ✅ Complete | Core LangGraph pipeline, 6 specialist agents |
| **Phase 1.5** | ✅ Complete | Sector-aware prompts for 7 industry verticals |
| **Phase 2** | ✅ Complete | Competitor Intel Agent + Risk Scoring Engine |
| **Phase 3** | 🔄 In Progress | Document RAG with ChromaDB (upload pitch decks) |
| **Phase 4** | 📋 Planned | SQLite persistence + run history + report comparison |
| **Phase 5** | 📋 Planned | ReAct Q&A agent with LangGraph subgraph |
| **Phase 6** | 📋 Planned | LangSmith observability wired into Streamlit UI |
| **Phase 7** | 📋 Planned | APScheduler monitoring + email/Slack alerts |
| **Phase 8** | 📋 Planned | PDF export + polish + production deployment |

---

## 🔧 Configuration Reference

All configuration is managed through environment variables in `.env`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | — | Primary LLM. Free at console.groq.com |
| `GOOGLE_API_KEY` | Recommended | — | Fallback LLM when Groq rate-limits |
| `FIRECRAWL_API_KEY` | Optional | — | Better scraping. Falls back to Playwright |
| `LANGCHAIN_API_KEY` | Optional | — | LangSmith tracing |
| `LANGCHAIN_TRACING_V2` | Optional | `false` | Set `true` to enable traces |
| `LANGCHAIN_PROJECT` | Optional | `intellidd-pro` | LangSmith project name |
| `MAX_WORKERS` | Optional | `7` | Parallel agent threads |
| `AGENT_TIMEOUT_SECONDS` | Optional | `90` | Per-agent timeout |
| `DB_PATH` | Optional | `./intellidd.db` | SQLite database path |
| `CHROMA_PATH` | Optional | `./chroma_store` | ChromaDB persistence dir |
| `ALERT_EMAIL_FROM` | Optional | — | Gmail for monitoring alerts |
| `ALERT_SLACK_WEBHOOK` | Optional | — | Slack incoming webhook URL |

---

## 🧠 How Rate Limits Are Handled

IntelliDD Pro has a built-in **3-layer rate limit protection** in `tools/llm_factory.py`:

1. **Stagger delay** — each parallel agent waits `random(0.5, 2.5)s` before calling the LLM, preventing TPM burst
2. **Smart retry** — parses Groq's `"Please try again in 1.93s"` error message and waits exactly that long (+ buffer)
3. **Exponential backoff** — if no wait time is provided, waits 5s → 10s → 20s → 40s across up to 5 attempts
4. **Automatic fallback** — if Groq is exhausted for the day, switches to Gemini via LangChain's `.with_fallbacks()`

---

## 🤝 Contributing

Contributions are welcome! This is an active portfolio project being built phase by phase.

```bash
# Fork and clone
git clone https://github.com/yourusername/intellidd-pro.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Install dev dependencies
uv sync --dev

# Run linting
uv run black .
uv run isort .

# Run tests
uv run pytest tests/
```

**Areas where contributions are especially welcome:**
- Additional sector prompts (Marketplace, GovTech, EdTech as standalone, etc.)
- New specialist agents (Legal/Regulatory, ESG/Sustainability)
- Better competitor discovery logic
- UI improvements to the Streamlit frontend
- Test coverage for agents and pipeline

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by [`awesome-ai-apps/due_diligence_agent`](https://github.com/Arindam200/awesome-ai-apps/tree/main/advance_ai_agents/due_diligence_agent) by [@Arindam200](https://github.com/Arindam200)
- Built with [LangGraph](https://langchain-ai.github.io/langgraph/) by LangChain
- LLM inference powered by [Groq](https://groq.com) (free tier)
- Agent observability via [LangSmith](https://smith.langchain.com)

---

<div align="center">

**Built as a portfolio project demonstrating production-grade agentic AI engineering.**

*Multi-agent orchestration · Agentic RAG · LangGraph · Free-tier LLMs · Quantitative risk scoring*

<br/>

⭐ **Star this repo if you found it useful** ⭐

</div>