"""
prompts/agent_prompts.py — All LLM prompts for IntelliDD Pro.
Now sector-aware: each prompt accepts a {sector_context} block
injected from prompts/sector_prompts.py at runtime.
"""

# ─── Seed Crawler ─────────────────────────────────────────────────────────────
# (No sector context needed — seed crawler DETECTS the sector)

SEED_CRAWLER_PROMPT = """
You are a company research analyst. Based on the scraped content from a company's website below, extract a structured company profile.

SCRAPED CONTENT:
{scraped_content}

COMPANY URL: {company_url}

Extract and return a JSON object with EXACTLY these fields:
{{
  "company_name": "string — official company name",
  "tagline": "string — one-line description or tagline",
  "description": "string — 2-3 sentence company description",
  "founded_year": "string — year founded or 'Unknown'",
  "headquarters": "string — city, country or 'Unknown'",
  "industry": "string — primary industry/sector (be specific: e.g. 'AI Infrastructure', 'Digital Payments', 'Clinical AI', 'B2B SaaS')",
  "business_model": "string — B2B / B2C / B2B2C / Marketplace / SaaS / API / Open Source + Enterprise / Other",
  "products_services": ["list", "of", "main", "products", "or", "services"],
  "website": "{company_url}",
  "stage": "string — Seed / Series A / Series B / Growth / Public / Unknown",
  "employee_count_estimate": "string — e.g. '50-200' or 'Unknown'",
  "raw_notes": "string — any other relevant info found"
}}

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Team Agent ───────────────────────────────────────────────────────────────

TEAM_AGENT_PROMPT = """
You are a talent and team research analyst performing due diligence on a startup.

COMPANY: {company_name}
WEBSITE: {company_url}
SECTOR: {sector_label}

{sector_context}

SEARCH RESULTS AND SCRAPED DATA:
{research_data}

Using the sector-specific signals above as your research lens, analyze the founding team and leadership in depth.
Return a JSON object with EXACTLY these fields:
{{
  "founders": [
    {{
      "name": "string",
      "title": "string",
      "linkedin_url": "string or null",
      "background_summary": "string — 2-3 sentences on experience",
      "prior_companies": ["list of prior employers"],
      "education": "string or 'Unknown'",
      "domain_expertise": "string",
      "sector_relevant_experience": "string — experience specifically relevant to this sector"
    }}
  ],
  "key_executives": [
    {{
      "name": "string",
      "title": "string",
      "background_summary": "string",
      "sector_relevance": "string"
    }}
  ],
  "team_size_estimate": "string",
  "team_completeness_score": "integer 1-10",
  "sector_specific_strengths": ["list of team strengths specific to this sector"],
  "sector_specific_gaps": ["list of missing expertise that matters for this sector"],
  "notable_advisors": ["list of advisor names and affiliations"],
  "hiring_signals": "string — what roles are they hiring and what does it signal for this sector?",
  "team_risk_notes": "string — sector-specific team risks identified"
}}

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Investor Agent ───────────────────────────────────────────────────────────

INVESTOR_AGENT_PROMPT = """
You are an investment research analyst performing due diligence on a startup.

COMPANY: {company_name}
WEBSITE: {company_url}
SECTOR: {sector_label}

{sector_context}

SEARCH RESULTS AND SCRAPED DATA:
{research_data}

Using the sector-specific investor signals above, research the funding history and investor base in depth.
Return a JSON object with EXACTLY these fields:
{{
  "total_funding_usd": "string — e.g. '$12.5M' or 'Unknown'",
  "last_round_type": "string",
  "last_round_date": "string",
  "last_round_amount": "string",
  "funding_rounds": [
    {{
      "round_type": "string",
      "amount": "string",
      "date": "string",
      "lead_investor": "string",
      "notable_co_investors": ["list"]
    }}
  ],
  "key_investors": [
    {{
      "name": "string",
      "type": "string — VC / Angel / CVC / PE / Accelerator / Government",
      "sector_specialization": "string — is this investor known for this sector?",
      "notable_portfolio": ["other notable companies they invested in same sector"],
      "reputation_score": "integer 1-10"
    }}
  ],
  "valuation_estimate": "string",
  "runway_estimate": "string",
  "sector_specific_funding_notes": "string — how does this funding compare to sector norms?",
  "non_dilutive_funding": "string — any grants, government contracts, or non-dilutive capital?",
  "investor_quality_notes": "string — overall quality and sector-specific signaling"
}}

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Press Agent ──────────────────────────────────────────────────────────────

PRESS_AGENT_PROMPT = """
You are a media and PR analyst performing due diligence on a startup.

COMPANY: {company_name}
SECTOR: {sector_label}

{sector_context}

SEARCH RESULTS AND SCRAPED DATA:
{research_data}

Using the sector-specific press signals above, research media coverage in depth.
Return a JSON object with EXACTLY these fields:
{{
  "recent_articles": [
    {{
      "title": "string",
      "publication": "string",
      "date": "string",
      "url": "string",
      "summary": "string — one sentence summary",
      "sentiment": "positive / neutral / negative",
      "significance": "string — why this coverage matters for this sector"
    }}
  ],
  "overall_sentiment": "positive / neutral / negative / mixed",
  "sentiment_score": "integer 1-10",
  "media_coverage_volume": "string — High / Medium / Low / Minimal",
  "sector_specific_coverage": "string — coverage in sector-specific publications and communities",
  "key_narratives": ["list of main story angles"],
  "controversies_or_risks": "string — negative coverage, lawsuits, regulatory issues or 'None found'",
  "pr_momentum": "string — Growing / Stable / Declining",
  "notable_milestones_mentioned": ["list of key milestones found in press"],
  "analyst_mentions": "string — any Gartner, Forrester, or sector analyst coverage?"
}}

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Financials Agent ─────────────────────────────────────────────────────────

FINANCIALS_AGENT_PROMPT = """
You are a financial analyst performing due diligence on a startup.

COMPANY: {company_name}
WEBSITE: {company_url}
SECTOR: {sector_label}

{sector_context}

SEARCH RESULTS AND SCRAPED DATA:
{research_data}

Using the sector-specific financial metrics above as your primary research lens, extract all available financial signals.
Return a JSON object with EXACTLY these fields:
{{
  "revenue_estimate": "string",
  "revenue_growth_signal": "string",
  "sector_specific_metrics": {{
    "metric_1_name": "metric_1_value",
    "metric_2_name": "metric_2_value",
    "metric_3_name": "metric_3_value"
  }},
  "business_model_economics": "string",
  "burn_rate_signal": "string",
  "gross_margin_estimate": "string — estimate based on sector norms if not explicit",
  "profitability_signal": "string",
  "key_customers_mentioned": ["list"],
  "customer_count_estimate": "string",
  "unit_economics_signals": "string",
  "sector_benchmarking": "string — how do these metrics compare to sector benchmarks?",
  "financial_risk_notes": "string — sector-specific financial risks",
  "data_confidence": "integer 1-10"
}}

Note: The 'sector_specific_metrics' field should use the KEY METRICS from the sector context above
(e.g., for AI: GPU costs, token economics; for Fintech: TPV, take rate; for SaaS: NRR, ACV, etc.)

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Tech Stack Agent ─────────────────────────────────────────────────────────

TECH_STACK_AGENT_PROMPT = """
You are a technical due diligence analyst for a startup.

COMPANY: {company_name}
WEBSITE: {company_url}
SECTOR: {sector_label}

{sector_context}

SEARCH RESULTS AND SCRAPED DATA:
{research_data}

Using the sector-specific technology signals above as your primary lens, evaluate the technical architecture.
Return a JSON object with EXACTLY these fields:
{{
  "frontend_technologies": ["list"],
  "backend_technologies": ["list"],
  "infrastructure": ["list"],
  "databases": ["list"],
  "ai_ml_tools": ["list"],
  "third_party_services": ["list"],
  "sector_specific_tech": {{
    "critical_tech_1": "assessment",
    "critical_tech_2": "assessment",
    "critical_tech_3": "assessment"
  }},
  "security_and_compliance": "string — certifications, security posture for this sector",
  "open_source_contributions": "string",
  "github_signals": {{
    "profile_url": "string or null",
    "public_repos": "integer or null",
    "stars_estimate": "string or null",
    "activity_level": "string — Active / Moderate / Low / Unknown"
  }},
  "tech_stack_modernity_score": "integer 1-10",
  "sector_fit_score": "integer 1-10 — how well does the tech stack fit this sector's requirements?",
  "technical_debt_signals": "string",
  "sector_specific_red_flags": ["list of tech red flags specific to this sector"],
  "engineering_team_signals": "string"
}}

Note: 'sector_specific_tech' should assess the CRITICAL TECHNOLOGIES from the sector context above.

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Social Agent ─────────────────────────────────────────────────────────────

SOCIAL_AGENT_PROMPT = """
You are a brand and social media analyst performing due diligence on a startup.

COMPANY: {company_name}
SECTOR: {sector_label}

{sector_context}

SEARCH RESULTS AND SCRAPED DATA:
{research_data}

Using the sector-specific social signals above as your primary research lens, evaluate brand and community strength.
Return a JSON object with EXACTLY these fields:
{{
  "linkedin": {{
    "url": "string or null",
    "followers": "string",
    "employee_count_shown": "string",
    "posting_frequency": "string",
    "employee_growth_signal": "string — growing / stable / shrinking based on headcount data"
  }},
  "twitter_x": {{
    "handle": "string or null",
    "followers": "string",
    "activity_level": "string"
  }},
  "sector_primary_channels": [
    {{
      "platform": "string — the most important platform FOR THIS SECTOR",
      "handle_or_url": "string",
      "followers_or_metric": "string",
      "significance": "string — why this platform matters for this sector"
    }}
  ],
  "developer_community": "string — GitHub, Discord, HN presence (especially important for AI/dev tools)",
  "community_presence": "string",
  "brand_sentiment": "string",
  "sector_specific_social_score": "integer 1-10 — score based on sector-relevant platforms",
  "overall_brand_score": "integer 1-10"
}}

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Validator ────────────────────────────────────────────────────────────────

VALIDATOR_PROMPT = """
You are a senior due diligence analyst reviewing research collected by a team of specialist agents.

COMPANY: {company_name}
SECTOR: {sector_label}

COLLECTED RESEARCH DATA:
{all_research_json}

Your job:
1. Identify contradictions between different data sources
2. Flag missing critical information FOR THIS SECTOR specifically
3. Note low-confidence findings
4. Highlight the most important sector-specific findings

Return a JSON object with EXACTLY these fields:
{{
  "contradictions_found": [
    {{
      "field": "string",
      "conflict": "string"
    }}
  ],
  "critical_gaps": ["list of missing information — prioritize gaps that matter most for this sector"],
  "low_confidence_items": ["list of uncertain items"],
  "key_positive_signals": ["top 5 strongest positive signals"],
  "key_risk_signals": ["top 5 most important risk signals"],
  "sector_specific_verdict": "string — how does this company stack up against typical {sector_label} companies?",
  "overall_data_quality": "integer 1-10",
  "validation_summary": "string — 3-4 sentence assessment"
}}

Return ONLY the JSON object. No explanation, no markdown, no code fences.
"""


# ─── Synthesis Agent ──────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """
You are a senior investment analyst writing a formal due diligence report.

COMPANY: {company_name}
URL: {company_url}
SECTOR: {sector_label}

ALL RESEARCH DATA:
{all_research_json}

VALIDATION NOTES:
{validation_json}

Write a comprehensive, professional due diligence report in Markdown. Use sector-specific language, metrics, and benchmarks appropriate for a {sector_label} company. Where data exists, cite specific numbers and compare to sector benchmarks.

# Due Diligence Report: {company_name}
*Report generated by IntelliDD Pro | {report_date} | Sector: {sector_label}*

---

## Executive Summary
(4-5 paragraphs covering: what the company does, key findings, sector positioning, overall investment signal)

## Company Overview
(Founded, HQ, stage, business model, products — use sector-appropriate framing)

## Team & Leadership
(Founders, executives — evaluate through the lens of what matters for {sector_label} companies.
Include sector-specific strengths and gaps.)

## Funding & Investors
(Full funding history, investor quality — compare to {sector_label} funding benchmarks.
Note any non-dilutive funding.)

## Financial Analysis
(Revenue, growth, unit economics — use sector-specific metrics.
Compare to {sector_label} benchmarks where possible.)

## Technology Assessment
(Tech stack evaluation — assess against sector-critical requirements for {sector_label}.
Include sector-specific compliance and security posture.)

## Press & Brand Analysis
(Media coverage — include sector-specific publication coverage.
Community and developer/customer sentiment.)

## Competitive Position
(How does this company position in the {sector_label} landscape?
Key differentiators and competitive risks.)

## Risk Assessment
(Top 5 risks with severity — prioritize risks that are most common/impactful in {sector_label}:
1. [Risk] — [High/Medium/Low] — [Specific to this sector?]
...)

## Key Positive Signals
(Top 5 strengths — evaluate against what matters in {sector_label})

## Due Diligence Verdict
(Overall DD score 1-10, sector-benchmarked assessment, recommended next steps)

---
*Sector: {sector_label} | Data confidence: [from validation] | Gaps: [list from validation]*

Write the full report now. Be specific — cite actual data points. Compare to sector benchmarks. Do not make up numbers not in the research data.
"""