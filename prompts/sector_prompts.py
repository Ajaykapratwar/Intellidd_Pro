"""
prompts/sector_prompts.py — Sector-specific research signals for each agent.

Each function returns a string that gets injected into the agent's base prompt
as a "SECTOR-SPECIFIC RESEARCH FOCUS" block.

This tells the LLM:
  - Which metrics actually matter for this sector
  - What specific signals to look for
  - What red flags are common in this sector
  - Which data sources are most relevant
"""

from prompts.sectors import Sector


# ══════════════════════════════════════════════════════════════════════════════
#  TEAM AGENT — Sector-specific team signals
# ══════════════════════════════════════════════════════════════════════════════

TEAM_SECTOR_CONTEXT: dict[Sector, str] = {

    Sector.AI_TECH: """
SECTOR: AI / Developer Tools / Cloud Infrastructure

TEAM SIGNALS TO PRIORITIZE:
- Research publications: Are founders published in top ML venues (NeurIPS, ICML, ICLR, ACL)?
- Prior AI company experience: DeepMind, OpenAI, Google Brain, Meta AI, Anthropic alumni?
- Open source credibility: Personal GitHub stars, well-known OSS contributions?
- Academic pedigree: PhD from top CS programs (MIT, Stanford, CMU, ETH Zurich)?
- Developer community respect: Followers on HuggingFace, GitHub, Twitter/X among ML community?
- Technical founder ratio: Is the team majority technical vs. business? (should be high for AI)
- AI safety/ethics awareness: Any public work on responsible AI, alignment?

RED FLAGS FOR THIS SECTOR:
- No technical co-founder — business-only founding team in an AI company is a serious concern
- Founders who only use AI tools but have no ML research/engineering depth
- Team with no prior experience shipping to developers or enterprise
- No published work or open source contributions in the claimed AI domain
""",

    Sector.FINTECH: """
SECTOR: Financial Technology / Payments / Banking / Insurance

TEAM SIGNALS TO PRIORITIZE:
- Regulatory experience: Has the team navigated banking licenses, PCI DSS, SOC 2, FCA, RBI?
- Prior fintech exits: Any founders from Stripe, Razorpay, Brex, Plaid, Chime, Robinhood?
- Banking/finance background: Ex-Goldman Sachs, JPMorgan, Visa, Mastercard on the team?
- Sales/BD experience: Enterprise fintech needs strong B2B sales DNA in leadership
- Compliance officers: Is there a dedicated Chief Compliance Officer or Legal counsel?
- Risk management expertise: Critical for lending, insurance, and payments companies

RED FLAGS FOR THIS SECTOR:
- No compliance or legal expertise in leadership for a regulated product
- Founders with no prior financial services exposure building a bank or lender
- Team with no experience closing enterprise contracts (if B2B fintech)
- Missing CFO or finance function for a company handling real money
""",

    Sector.HEALTHCARE: """
SECTOR: Healthcare / Biotech / Pharmaceutical / Medical Technology

TEAM SIGNALS TO PRIORITIZE:
- Clinical/medical credentials: Are there MDs, PhDs, or clinicians on the founding team?
- Regulatory experience: FDA 510(k), CE marking, HIPAA compliance, IRB approvals?
- Prior healthtech/pharma experience: Previous roles at J&J, Roche, Epic Systems, Veeva?
- KOL relationships: Key Opinion Leader doctors or hospital system advisors on board?
- Drug discovery depth: For biotech — publication record in relevant therapeutic area?
- Health system sales experience: Long healthcare sales cycles require specialized expertise

RED FLAGS FOR THIS SECTOR:
- No clinical advisor or medical advisor for a patient-facing or clinical product
- Team claiming FDA clearance pathway without regulatory affairs expertise
- No healthcare data security/HIPAA expertise for a health data company
- Business-only team for a drug discovery or medical device company
""",

    Sector.SAAS_ENTERPRISE: """
SECTOR: B2B SaaS / Enterprise Software / Cybersecurity

TEAM SIGNALS TO PRIORITIZE:
- Enterprise sales DNA: Prior VP Sales, CRO, or AE experience at Salesforce, Workday, ServiceNow?
- Product-led growth experience: For PLG SaaS — prior experience at Slack, Figma, Notion?
- Domain expertise: Do founders have deep expertise in the problem they're solving (ex-practitioners)?
- Customer success track record: Evidence of managing large enterprise accounts
- Technical security credibility: For cybersecurity — prior experience at CrowdStrike, Palo Alto, etc.?
- Go-to-market sophistication: Channel partner strategy, system integrator relationships?

RED FLAGS FOR THIS SECTOR:
- Technical-only founding team with no enterprise sales experience (for mid-market/enterprise SaaS)
- No domain expertise — building HR software without having worked in HR
- Missing VP of Sales hire for a company targeting enterprise deals above $50K ACV
""",

    Sector.ECOMMERCE: """
SECTOR: E-commerce / Marketplace / Retail / Logistics

TEAM SIGNALS TO PRIORITIZE:
- Marketplace/logistics operations experience: Prior roles at Amazon, Shopify, Flipkart, Instacart?
- Supply chain expertise: For logistics/fulfillment companies — operations depth is critical
- GMV track record: Has the team scaled a marketplace to significant GMV before?
- Category expertise: Do founders have deep knowledge of the specific product category?
- Growth/performance marketing expertise: D2C requires strong paid acquisition DNA

RED FLAGS FOR THIS SECTOR:
- No operations or logistics expertise for a fulfillment or delivery company
- Founders with no prior e-commerce or retail experience building a marketplace
- No clear supply-side or demand-side acquisition strategy in leadership DNA
""",

    Sector.CONSUMER: """
SECTOR: Consumer Apps / Social / Gaming / Media / EdTech

TEAM SIGNALS TO PRIORITIZE:
- Viral/growth product experience: Prior product roles at TikTok, Instagram, Snapchat, Discord?
- Content/community building: Evidence of building engaged user communities before
- Gaming-specific: For gaming — prior studio experience, shipped titles, player acquisition?
- EdTech: Pedagogy experts or former educators combined with product engineers?
- Creator economy: Network of creators, influencers, or content partners?

RED FLAGS FOR THIS SECTOR:
- No consumer product experience in a founding team building a social/consumer app
- No growth hacking or viral loop understanding in the team
- EdTech team with no educators or learning science expertise
""",

    Sector.DEEPTECH: """
SECTOR: Deep Tech / Robotics / Hardware / CleanTech / Space

TEAM SIGNALS TO PRIORITIZE:
- Hands-on hardware/engineering experience: PhDs, prior roles at SpaceX, Tesla, Boston Dynamics?
- Patent portfolio: Filed or granted patents in the core technology area?
- Manufacturing experience: Scale-up from prototype to production is the key challenge
- Government/defense contracts: Important revenue signal for defense or space tech
- Physics/chemistry/materials science depth: For advanced materials or energy companies

RED FLAGS FOR THIS SECTOR:
- Software-only team attempting to build hardware without manufacturing expertise
- No IP protection strategy for a deep tech company with defensible technology
- Team with no experience navigating long development cycles (5-10 years for some deep tech)
""",

    Sector.GENERAL: """
SECTOR: Technology / Software

TEAM SIGNALS TO PRIORITIZE:
- Prior startup experience: Have founders built and scaled companies before?
- Domain expertise: Do they have deep knowledge of the problem space?
- Technical vs. business balance: Is the team appropriately balanced?
- Advisor quality: Are there relevant advisors filling expertise gaps?
- Hiring velocity: What roles are they hiring? Does it match stated priorities?

RED FLAGS:
- Single founder with no co-founder or advisor support
- No domain expertise in the core market
- Team that has pivoted multiple times without traction
""",
}


# ══════════════════════════════════════════════════════════════════════════════
#  INVESTOR AGENT — Sector-specific funding signals
# ══════════════════════════════════════════════════════════════════════════════

INVESTOR_SECTOR_CONTEXT: dict[Sector, str] = {

    Sector.AI_TECH: """
SECTOR: AI / Developer Tools / Cloud Infrastructure

INVESTOR SIGNALS TO PRIORITIZE:
- Tier-1 AI-specialist VCs: a16z, Sequoia, Accel, Index Ventures, Coatue, Khosla Ventures?
- Strategic corporate investors: Google Ventures, Microsoft M12, Nvidia, Salesforce Ventures?
- AI-focused accelerators: Y Combinator, AI2 Incubator, Entrepreneur First?
- Valuation multiples: AI companies often see 20-50x ARR multiples at growth stage
- Developer tooling investment pace: Is this space getting competitive? (signals market validation)
- Open source monetization strategy: How does the funding narrative align with OSS business model?

SECTOR BENCHMARKS:
- Seed: $2-5M for AI infra, $500K-2M for AI apps
- Series A: $10-25M typical for developer tools with traction
- Revenue multiple at Series B+: 15-30x ARR is normal for AI infrastructure
""",

    Sector.FINTECH: """
SECTOR: Financial Technology / Payments / Banking / Insurance

INVESTOR SIGNALS TO PRIORITIZE:
- Fintech-specialist VCs: Ribbit Capital, Bain Capital Ventures, QED Investors, Accel?
- Banking partners as investors: Is a bank or card network (Visa, Mastercard) on the cap table?
- Regulatory-aware investors: Investors with portfolio experience navigating financial regulation?
- Revenue-based financing: Some fintech companies use RBF — is this on the cap table?
- Valuation context: Fintech valuations compressed significantly post-2021 — what's the entry point?

SECTOR BENCHMARKS:
- Payments/lending: Often capital-intensive, look for debt facility size alongside equity
- Neobanks: Regulatory capital requirements add to burn rate
- B2B fintech SaaS: 10-20x ARR multiples more typical (vs 30x+ for AI)
""",

    Sector.HEALTHCARE: """
SECTOR: Healthcare / Biotech / Pharmaceutical / Medical Technology

INVESTOR SIGNALS TO PRIORITIZE:
- Healthcare-specialist VCs: a16z Bio, GV (Google Ventures), OrbiMed, Andreessen Horowitz Bio?
- Non-dilutive funding: NIH grants, SBIR/STTR grants (major signal for biotech credibility)
- Strategic health system investors: Hospital systems or payer (insurance) investors on cap table?
- Pharma partnerships: Milestone-based deals with Big Pharma as a funding signal?
- Clinical trial funding: Is capital specifically earmarked for clinical trials?

SECTOR BENCHMARKS:
- Drug discovery: $20-100M+ Series A is normal given long timelines
- Digital health SaaS: More similar to regular SaaS ($5-15M Series A)
- Medical devices: FDA clearance milestone often gate for Series B
""",

    Sector.SAAS_ENTERPRISE: """
SECTOR: B2B SaaS / Enterprise Software / Cybersecurity

INVESTOR SIGNALS TO PRIORITIZE:
- SaaS-specialist VCs: Bessemer Venture Partners, Insight Partners, Battery Ventures, Tiger Global?
- Customer reference investors: Existing enterprise customers who also invested?
- ARR-based metrics at each round:
  - Seed: Pre-revenue to $500K ARR
  - Series A: $1-5M ARR, strong NRR
  - Series B: $5-20M ARR, clear go-to-market motion
- Net Revenue Retention (NRR): Best SaaS companies show >120% NRR
- Rule of 40: Growth rate + profit margin should exceed 40

SECTOR BENCHMARKS:
- Typical Series A valuation: 10-20x forward ARR
- Cybersecurity premium: 15-25x ARR due to non-discretionary spend nature
""",

    Sector.ECOMMERCE: """
SECTOR: E-commerce / Marketplace / Retail / Logistics

INVESTOR SIGNALS TO PRIORITIZE:
- GMV-focused investors: Tiger Global, SoftBank Vision Fund, Sequoia for large marketplaces?
- Strategic retail investors: Existing retailers investing as a strategic partnership signal?
- Logistics investors: Dedicated supply chain / logistics VCs like DBL Partners?
- Take rate: What % of GMV does the platform take? (marketplace health metric)
- Unit economics focus: CAC, payback period, contribution margin per order

SECTOR BENCHMARKS:
- Marketplaces valued on GMV multiple (0.5-3x GMV typically)
- Logistics: Capital intensive, often requires debt alongside equity
""",

    Sector.CONSUMER: """
SECTOR: Consumer Apps / Social / Gaming / Media / EdTech

INVESTOR SIGNALS TO PRIORITIZE:
- Consumer-focused VCs: Benchmark, Founders Fund, Lightspeed, General Catalyst?
- DAU/MAU ratio as investment thesis signal: >50% is excellent for social/consumer
- App store ranking trends at time of investment?
- Gaming: Revenue split between in-app purchases, ads, subscriptions?
- EdTech: B2C vs B2B2C model — B2B2C (selling to schools) has better unit economics

SECTOR BENCHMARKS:
- Consumer apps: Often valued on DAU, not ARR (especially pre-monetization)
- Gaming: Revenue multiples vary widely (2-10x depending on genre and growth)
""",

    Sector.DEEPTECH: """
SECTOR: Deep Tech / Robotics / Hardware / CleanTech / Space

INVESTOR SIGNALS TO PRIORITIZE:
- Government grants: DARPA, DOE, NASA contracts as non-dilutive validation?
- Corporate strategic investors: Defense primes, energy companies as strategic investors?
- Patient capital: Long-horizon funds (Breakthrough Energy, Lux Capital, Prime Movers Lab)?
- Milestone-based funding: Is capital tied to specific technical milestones?
- Hardware premium: Deep tech typically raises more at each stage than software

SECTOR BENCHMARKS:
- Robotics/hardware: Series A often $15-40M (higher capex needs)
- CleanTech: Mix of equity + project finance + government grants
- Space: Highly variable; SpaceX-style moonshots vs. smaller satellite SaaS
""",

    Sector.GENERAL: """
SECTOR: Technology / Software

INVESTOR SIGNALS TO PRIORITIZE:
- Investor reputation and network value beyond capital
- Stage-appropriate fund size (seed fund vs. growth fund investing)
- Portfolio synergies: Do other portfolio companies create partnership opportunities?
- Follow-on rate: Have existing investors participated in follow-on rounds?

SECTOR BENCHMARKS:
- Evaluate funding amount against team size and 18-month runway needs
- Revenue multiple appropriate to growth rate and gross margins
""",
}


# ══════════════════════════════════════════════════════════════════════════════
#  FINANCIALS AGENT — Sector-specific financial metrics
# ══════════════════════════════════════════════════════════════════════════════

FINANCIALS_SECTOR_CONTEXT: dict[Sector, str] = {

    Sector.AI_TECH: """
SECTOR: AI / Developer Tools / Cloud Infrastructure

KEY METRICS TO RESEARCH:
- ARR / MRR: API usage-based revenue vs. seat-based subscriptions — which model?
- Gross margins: AI infra companies often have 60-80% gross margins; AI apps can be lower due to inference costs
- Token/compute costs: What is their cost per inference call? Is this sustainable?
- Developer adoption: Number of API calls/month, active developers, models hosted
- Open source vs. paid conversion rate: What % of OSS users convert to paid?
- Enterprise vs. self-serve revenue split
- GPU/compute cost as % of revenue: High GPU costs compress margins

FINANCIAL RED FLAGS FOR THIS SECTOR:
- Negative gross margins due to compute costs (common early stage but unsustainable)
- 100% reliance on one cloud provider creating cost concentration risk
- Free tier subsidy that doesn't convert — high compute costs with no paid conversion path
""",

    Sector.FINTECH: """
SECTOR: Financial Technology / Payments / Banking / Insurance

KEY METRICS TO RESEARCH:
- Total Payment Volume (TPV) or Gross Merchandise Value (GMV): Overall transaction flow
- Take rate / Net revenue rate: Revenue as % of TPV (Stripe ~2.9%, typical)
- Net Interest Margin (NIM): For neobanks/lenders — spread between lending and deposit rates
- Loss rate / Default rate: For lending companies — critical risk metric
- Customer Acquisition Cost (CAC) and Payback Period: Financial services CAC can be very high
- Regulatory capital requirements: How much capital must be held vs. deployed?
- Churn rate on financial products: Much stickier than typical SaaS if core banking
- AUM / Loans Under Management: For wealth management / lending platforms

FINANCIAL RED FLAGS FOR THIS SECTOR:
- Rising default rates in a lending portfolio
- CAC exceeding 12-month LTV
- Regulatory capital below required minimums
- Revenue recognition issues (interchange vs. net revenue reporting)
""",

    Sector.HEALTHCARE: """
SECTOR: Healthcare / Biotech / Pharmaceutical / Medical Technology

KEY METRICS TO RESEARCH:
- Clinical milestones: Phase I/II/III trial completion (biotech)
- Reimbursement status: Is the product covered by insurance/Medicare/Medicaid?
- Revenue model: Fee-for-service vs. value-based care vs. SaaS subscription?
- Patient outcomes data: Clinical evidence supporting the product's efficacy
- Hospital/payer contract values: Enterprise healthcare deals are multi-year
- Drug royalty rates: If licensing technology — what are the royalty terms?
- Cash runway to next clinical milestone: Critical for biotech investors

FINANCIAL RED FLAGS FOR THIS SECTOR:
- No clear reimbursement pathway for a clinical product
- Biotech company with <18 months runway before next clinical readout
- Revenue solely from grants (not yet commercial — flag for digital health)
- Single-payer concentration risk (one insurance company = 80% of revenue)
""",

    Sector.SAAS_ENTERPRISE: """
SECTOR: B2B SaaS / Enterprise Software / Cybersecurity

KEY METRICS TO RESEARCH:
- ARR and MRR: Monthly and annual recurring revenue figures
- Net Revenue Retention (NRR): >120% is excellent, <100% is dangerous
- Gross Revenue Retention (GRR): Should be >85% for enterprise SaaS
- Average Contract Value (ACV): SMB (<$10K), mid-market ($10-100K), enterprise (>$100K)?
- Sales cycle length: Enterprise SaaS typically 3-12 months
- CAC Payback Period: <18 months is healthy for SaaS
- Magic Number: Efficiency of sales spend (>1 is excellent)
- Rule of 40: Growth rate + FCF margin should exceed 40
- Gross margins: SaaS should be 70-85%

FINANCIAL RED FLAGS FOR THIS SECTOR:
- NRR below 100% — customers are churning or downgrading
- Gross margin below 60% (may indicate services-heavy revenue or high COGS)
- Sales cycle lengthening — sign of market demand softening
- CAC Payback exceeding 24 months
""",

    Sector.ECOMMERCE: """
SECTOR: E-commerce / Marketplace / Retail / Logistics

KEY METRICS TO RESEARCH:
- GMV (Gross Merchandise Value): Total value of transactions on platform
- Take rate: Platform revenue as % of GMV (varies 5-30% by category)
- Contribution margin per order: Revenue minus variable costs per transaction
- Average Order Value (AOV): And trend over time
- Repeat purchase rate / Cohort retention: Critical for D2C brands
- Customer Acquisition Cost by channel (paid, organic, social)
- Inventory turnover: For companies holding inventory
- Delivery/logistics cost per order: Key unit economic lever

FINANCIAL RED FLAGS FOR THIS SECTOR:
- Negative contribution margin per order (subsidizing growth)
- CAC exceeding 6-month LTV for a low-margin category
- High inventory write-offs or unsold stock
- Delivery cost inflation eroding margin
""",

    Sector.CONSUMER: """
SECTOR: Consumer Apps / Social / Gaming / Media / EdTech

KEY METRICS TO RESEARCH:
- DAU / MAU ratio (engagement metric — >50% is excellent)
- ARPU (Average Revenue Per User): Monthly and annual
- User acquisition cost by channel
- D1/D7/D30 retention: Day 1, 7, 30 retention cohorts
- LTV:CAC ratio: Should be >3x for sustainable consumer business
- Subscription conversion rate: Free-to-paid %
- Gaming: ARPPU (Average Revenue Per Paying User), payer conversion rate
- EdTech: Course completion rate (leading indicator of retention)

FINANCIAL RED FLAGS FOR THIS SECTOR:
- D30 retention below 20% (poor product-market fit)
- ARPU declining over time despite user growth
- Heavy paid UA spend with no organic growth
- LTV:CAC below 2x
""",

    Sector.DEEPTECH: """
SECTOR: Deep Tech / Robotics / Hardware / CleanTech / Space

KEY METRICS TO RESEARCH:
- Development stage: Pre-revenue / pilot / commercial? What's the revenue model?
- Government contract value: DARPA, DOE, NASA awards are major revenue signals
- Unit economics at scale: What does gross margin look like at production volumes?
- COGS trajectory: Manufacturing cost reduction curve as volumes increase
- CapEx requirements: Factory, tooling, equipment costs for manufacturing scale-up
- Patent licensing revenue: Are there royalty streams from IP licensing?
- R&D spend as % of revenue: Expect high (50-200% of revenue) for pre-commercial deeptech

FINANCIAL RED FLAGS FOR THIS SECTOR:
- Unit economics that don't improve with scale (no manufacturing learning curve)
- Capex requirements exceeding available capital
- Revenue solely from government grants with no commercial path
- Bill-of-materials cost higher than target selling price at scale
""",

    Sector.GENERAL: """
SECTOR: Technology / Software

KEY METRICS TO RESEARCH:
- Revenue model and primary revenue streams
- Revenue growth rate year-over-year
- Gross margin percentage
- Burn rate and runway
- Key customer concentration (any single customer >20% of revenue?)
- Pricing strategy signals from public information

FINANCIAL RED FLAGS:
- Revenue concentration in one customer
- Declining growth rate with increasing burn
- Gross margin below 40%
""",
}


# ══════════════════════════════════════════════════════════════════════════════
#  TECH STACK AGENT — Sector-specific technology signals
# ══════════════════════════════════════════════════════════════════════════════

TECH_SECTOR_CONTEXT: dict[Sector, str] = {

    Sector.AI_TECH: """
SECTOR: AI / Developer Tools / Cloud Infrastructure

TECH SIGNALS TO PRIORITIZE:
- Model architecture: Transformer-based? Proprietary architecture? Fine-tuned base models?
- Inference infrastructure: Custom CUDA kernels, vLLM, TensorRT, ONNX optimization?
- Training infrastructure: Multi-GPU / multi-node training? Which accelerators (H100, A100, TPU)?
- Model serving: Custom inference stack vs. vLLM vs. TGI (Text Generation Inference)?
- Vector stores: Pinecone, Weaviate, Qdrant, Chroma — signals RAG architecture maturity
- MLOps stack: Weights & Biases, MLflow, DVC — signal of ML engineering maturity
- Developer experience: SDK quality, API documentation, playground availability
- Open source strategy: Which repos? Stars? Contributors? Fork activity?
- Edge deployment: Any on-device or edge inference capabilities?

TECH RED FLAGS FOR THIS SECTOR:
- Fully API-dependent on OpenAI with no proprietary model work (low defensibility)
- No inference optimization — serving GPT-4 at retail API prices unsustainably
- Model outputs not evaluated systematically (no evals framework)
- Security gaps: No output filtering, no PII handling, no rate limiting on API
""",

    Sector.FINTECH: """
SECTOR: Financial Technology / Payments / Banking / Insurance

TECH SIGNALS TO PRIORITIZE:
- Payment processing: Stripe integration, direct card scheme membership, own acquiring?
- Core banking system: Modern (Thought Machine, Mambu) vs. legacy (FIS, Temenos)?
- Compliance tech: AML/KYC automation, sanctions screening (Chainalysis, ComplyAdvantage)?
- Security certifications: PCI DSS Level 1, SOC 2 Type II, ISO 27001?
- API connectivity: Open Banking APIs, Plaid/MX integration for account aggregation?
- Fraud detection: ML-based fraud models, rule engines, 3DS implementation?
- Encryption: End-to-end encryption, HSM usage for key management?
- Uptime SLA: Financial services need 99.99%+ uptime — what's their track record?

TECH RED FLAGS FOR THIS SECTOR:
- No mention of PCI DSS compliance for a payments company
- Using legacy core banking with no modernization path
- No fraud detection or AML system mentioned
- Single cloud provider with no disaster recovery or multi-region setup
""",

    Sector.HEALTHCARE: """
SECTOR: Healthcare / Biotech / Pharmaceutical / Medical Technology

TECH SIGNALS TO PRIORITIZE:
- HIPAA compliance: PHI handling, BAA agreements, audit logging?
- HL7 FHIR integration: Standard for EHR interoperability — critical for health IT
- EHR integrations: Epic, Cerner, Allscripts integration capabilities?
- Clinical AI validation: FDA SaMD (Software as a Medical Device) classification?
- Data de-identification: HIPAA Safe Harbor or Expert Determination methods?
- Clinical data standards: SNOMED CT, ICD-10, CPT coding support?
- Bioinformatics stack: For biotech — what computational biology tools are used?
- Lab information systems: LIMS integration for diagnostics companies?

TECH RED FLAGS FOR THIS SECTOR:
- No mention of HIPAA compliance for a company handling patient data
- No EHR integration strategy for a clinical workflow product
- AI/ML diagnostic tool with no FDA regulatory strategy
- Storing PHI without proper encryption and access controls
""",

    Sector.SAAS_ENTERPRISE: """
SECTOR: B2B SaaS / Enterprise Software / Cybersecurity

TECH SIGNALS TO PRIORITIZE:
- SSO/SAML support: Enterprise SaaS needs Okta/Azure AD integration
- SOC 2 Type II certification: Table stakes for enterprise sales
- Multi-tenancy architecture: True SaaS vs. single-tenant deployments?
- API-first design: Developer-friendly APIs enable customer integrations?
- Uptime SLA: 99.9%+ with status page transparency?
- Data residency: EU (GDPR), US, and regional data residency options?
- Enterprise features: Audit logs, RBAC, custom roles, admin controls?
- CI/CD maturity: Deployment frequency as a proxy for engineering velocity

TECH RED FLAGS FOR THIS SECTOR:
- No SOC 2 certification for enterprise sales
- No SSO/SAML support but targeting enterprise accounts
- Shared infrastructure with no tenant isolation
- No API or webhook support — limits customer integration capability
""",

    Sector.ECOMMERCE: """
SECTOR: E-commerce / Marketplace / Retail / Logistics

TECH SIGNALS TO PRIORITIZE:
- Platform architecture: Headless commerce, PWA, or traditional monolith?
- Payment stack: How many payment methods? Local payment methods for international?
- Inventory management: Real-time inventory sync, multi-warehouse support?
- Personalization: ML-based product recommendations, search ranking?
- Performance: Core Web Vitals, page speed (direct revenue impact in e-commerce)
- Fulfillment tech: WMS (Warehouse Management System), carrier integrations?
- Fraud prevention: Order fraud detection, chargeback management tools?

TECH RED FLAGS FOR THIS SECTOR:
- Slow page loads (>3s) — directly correlated with conversion rate drop
- No fraud detection for marketplace with high-value transactions
- Single payment method support limiting market reach
- No mobile-first design for a consumer marketplace
""",

    Sector.CONSUMER: """
SECTOR: Consumer Apps / Social / Gaming / Media / EdTech

TECH SIGNALS TO PRIORITIZE:
- Mobile-first: Native iOS/Android vs. React Native vs. Flutter?
- Recommendation engine: Algorithmic feed, content ranking, personalization?
- Content delivery: CDN usage, video streaming infrastructure?
- Push notification infrastructure: Engagement and retention driver
- A/B testing framework: Growth experimentation capability
- App Store ratings: iOS App Store and Google Play ratings and review sentiment
- Gaming-specific: Game engine (Unity, Unreal), server infrastructure for multiplayer?
- EdTech: LMS platform, content authoring tools, progress tracking?

TECH RED FLAGS FOR THIS SECTOR:
- Native app with consistently low App Store rating (<3.5 stars)
- No content moderation infrastructure for a social platform
- No offline mode for an app targeting markets with poor connectivity
- Game with server architecture that can't scale for launch-day traffic spikes
""",

    Sector.DEEPTECH: """
SECTOR: Deep Tech / Robotics / Hardware / CleanTech / Space

TECH SIGNALS TO PRIORITIZE:
- IP portfolio: Patent filings, patent grants, trade secrets strategy?
- Simulation environment: For robotics/autonomous — what sim-to-real tooling?
- Hardware BOM: Key components, supply chain risk, single-source dependencies?
- Manufacturing readiness: TRL (Technology Readiness Level) — where are they?
- Testing and validation: How is the hardware tested? Any safety certifications?
- Software stack for hardware: Embedded systems, firmware, real-time OS?
- Energy efficiency: Power consumption per unit of work (critical for CleanTech/edge hardware)
- Sensor fusion: For robotics/autonomous — camera, LiDAR, radar integration?

TECH RED FLAGS FOR THIS SECTOR:
- No patent protection for a hardware company claiming novel technology
- Single-source critical components with no alternative suppliers
- Technology Readiness Level below TRL 4 for a company claiming commercialization
- No systematic testing or safety validation for a safety-critical system
""",

    Sector.GENERAL: """
SECTOR: Technology / Software

TECH SIGNALS TO PRIORITIZE:
- Architecture modernity: Microservices vs. monolith — appropriate for current stage?
- Cloud infrastructure: AWS, GCP, or Azure? Multi-cloud or single-cloud?
- Security posture: Any known breaches, bug bounty program, security certifications?
- Development practices: Version control, CI/CD, code review process signals
- Scalability: Evidence of handling traffic growth without degradation
- Open source usage: Key dependencies and their license implications?

TECH RED FLAGS:
- Outdated technology stack with no modernization roadmap
- No security certifications for a company handling sensitive user data
- Single point of failure in critical infrastructure
""",
}


# ══════════════════════════════════════════════════════════════════════════════
#  PRESS AGENT — Sector-specific press signals
# ══════════════════════════════════════════════════════════════════════════════

PRESS_SECTOR_CONTEXT: dict[Sector, str] = {

    Sector.AI_TECH: """
SECTOR: AI / Developer Tools

KEY PRESS SIGNALS:
- Coverage in: TechCrunch, The Information, Wired, MIT Technology Review, VentureBeat AI?
- Benchmark comparisons: Is the company cited in model leaderboards (MMLU, HumanEval)?
- Academic citations: Is their work cited in research papers?
- Developer community coverage: Hacker News front page, r/MachineLearning discussion?
- Regulatory coverage: EU AI Act, US AI policy mentions?
- Controversy monitoring: Bias incidents, hallucination failures, safety concerns in press?
- Conference presence: NeurIPS, ICML, ICLR, AWS re:Invent mentions?
""",

    Sector.FINTECH: """
SECTOR: Fintech / Payments

KEY PRESS SIGNALS:
- Coverage in: Finextra, PYMNTS, American Banker, Banking Technology, The Block (crypto)?
- Regulatory news: Any central bank, FCA, RBI, SEC regulatory actions or approvals?
- Partnership announcements: Bank partnerships, card scheme deals (Visa/Mastercard)?
- Security incidents: Any data breaches, fraud incidents, outages in press?
- Awards: Finovate awards, Tearsheet awards — signal of industry recognition
- Customer case studies in financial trade press?
""",

    Sector.HEALTHCARE: """
SECTOR: Healthcare / Biotech

KEY PRESS SIGNALS:
- Coverage in: STAT News, FierceBiotech, BioPharma Dive, MedCity News, Health Affairs?
- Clinical trial results: Any published trial data in NEJM, JAMA, The Lancet?
- FDA news: Any 510(k) clearances, EUA grants, or warning letters?
- Partnership announcements: Hospital system deals, pharma partnerships?
- Reimbursement news: CMS coverage decisions, payer contract announcements?
- Patient advocacy coverage: Disease foundation endorsements?
""",

    Sector.SAAS_ENTERPRISE: """
SECTOR: B2B SaaS / Enterprise Software

KEY PRESS SIGNALS:
- Coverage in: G2, Gartner, Forrester analyst reports — major buying signal
- Magic Quadrant positioning: Gartner MQ or Forrester Wave inclusion?
- Customer win announcements: Enterprise customer logos in press releases?
- Partnership announcements: System integrator (Deloitte, Accenture) partnerships?
- Awards: Gartner Peer Insights, TrustRadius awards?
- Security certifications announced: SOC 2, ISO 27001 press releases?
""",

    Sector.ECOMMERCE: """
SECTOR: E-commerce / Marketplace / Retail

KEY PRESS SIGNALS:
- Coverage in: Modern Retail, Retail Dive, Business of Fashion, Internet Retailer?
- GMV milestones announced?
- Logistics partnerships: FedEx, UPS, DHL partnership announcements?
- Seller/merchant growth announcements?
- Holiday/seasonal performance coverage (Black Friday, Diwali)?
- Sustainability press: ESG initiatives for retail?
""",

    Sector.CONSUMER: """
SECTOR: Consumer Apps / Social / Gaming / Media

KEY PRESS SIGNALS:
- App Store chart rankings mentioned in coverage?
- Viral moments: TikTok trends, social media virality documented in press?
- Creator partnerships and influencer coverage?
- Coverage in: The Verge, Kotaku (gaming), EdSurge (EdTech)?
- Safety/moderation controversy: Any content moderation failures?
- Platform policy changes affecting the company?
""",

    Sector.DEEPTECH: """
SECTOR: Deep Tech / Robotics / Hardware / CleanTech

KEY PRESS SIGNALS:
- Coverage in: IEEE Spectrum, MIT Technology Review, CleanTechnica, Space News?
- Technical milestone announcements: First flight, first autonomous drive, first commercial deployment?
- Government contract announcements: DoD, DOE, NASA awards?
- Environmental impact coverage: Emissions reduction claims, third-party verification?
- Safety incident coverage: Any accidents or failures publicly reported?
- Standards body participation: IEEE, ISO standards committee involvement?
""",

    Sector.GENERAL: """
SECTOR: Technology / Software

KEY PRESS SIGNALS:
- Coverage volume and tier (tier-1 tech press vs. local/niche coverage)
- Funding announcement coverage
- Product launch coverage and reception
- Any controversies or negative coverage
- Award or recognition mentions
""",
}


# ══════════════════════════════════════════════════════════════════════════════
#  SOCIAL AGENT — Sector-specific social signals
# ══════════════════════════════════════════════════════════════════════════════

SOCIAL_SECTOR_CONTEXT: dict[Sector, str] = {

    Sector.AI_TECH: """
SECTOR: AI / Developer Tools

KEY SOCIAL SIGNALS:
- GitHub: Stars, forks, contributors, issues, PR velocity — the primary community signal for AI companies
- Hugging Face Hub: Model downloads, dataset downloads, Space likes?
- Hacker News: Posts, comment quality, founder engagement in HN threads?
- Discord: Developer community size, channel activity, support response time?
- Twitter/X: Following among AI researchers and ML engineers (quality > quantity)
- Papers With Code: Are they on PWC leaderboards?
- Substack/Newsletter: Do founders write technical content followed by practitioners?
""",

    Sector.FINTECH: """
SECTOR: Fintech / Payments

KEY SOCIAL SIGNALS:
- LinkedIn: Employee growth rate (strong hiring = growth signal)
- Twitter/X: Customer service response quality and speed
- Trustpilot / App Store reviews: Consumer-facing fintech must check these
- Reddit communities: r/personalfinance, r/investing community sentiment?
- LinkedIn Thought Leadership: Do executives post financial insights that get engagement?
- Glassdoor: Employee satisfaction — especially important for regulated financial companies
""",

    Sector.HEALTHCARE: """
SECTOR: Healthcare / Biotech

KEY SOCIAL SIGNALS:
- LinkedIn: Key hires from major health systems, pharma companies — signal of momentum
- PubMed/bioRxiv: Are they publishing preprints? Citation count?
- Patient community forums: PatientsLikeMe, HealthUnlocked — patient sentiment?
- Twitter/X: Engagement among physicians, nurses, healthcare executives?
- Conference presence: HIMSS, JPM Healthcare Conference, ASCO social buzz?
- Glassdoor: Important for biotech where talent competition is intense
""",

    Sector.SAAS_ENTERPRISE: """
SECTOR: B2B SaaS / Enterprise Software

KEY SOCIAL SIGNALS:
- G2/Capterra reviews: Rating, review volume, and recent review trend?
- LinkedIn company page growth and content engagement?
- Twitter/X: Customer success stories, product updates engagement?
- Community Slack/Discord: Active user community signals product stickiness?
- YouTube: Product demo views, tutorial channel activity?
- Glassdoor: Sales team morale and quota attainment signals from reviews?
""",

    Sector.ECOMMERCE: """
SECTOR: E-commerce / Marketplace / Retail

KEY SOCIAL SIGNALS:
- Instagram/TikTok: For D2C brands — follower count and content engagement rate?
- Pinterest: Product discovery channel strength?
- YouTube: Product review coverage by creators?
- Trustpilot/Google Reviews: Customer satisfaction scores?
- Reddit: Is the brand mentioned positively in relevant subreddits?
- Influencer partnerships: Documented collaborations in social media?
""",

    Sector.CONSUMER: """
SECTOR: Consumer Apps / Social / Gaming / Media

KEY SOCIAL SIGNALS:
- App Store rating and review volume on iOS and Android?
- TikTok/Instagram viral moments: User-generated content around the product?
- Discord/Reddit community size and activity?
- Twitch/YouTube streaming presence (for gaming companies)?
- Creator/influencer partnerships and organic endorsements?
- User-generated content volume as a virality signal?
""",

    Sector.DEEPTECH: """
SECTOR: Deep Tech / Robotics / Hardware / CleanTech

KEY SOCIAL SIGNALS:
- LinkedIn: Hiring velocity from top engineering universities (MIT, Stanford)?
- YouTube: Demo videos — views and engagement signal market interest?
- Academic Twitter/X: Citations by researchers in the field?
- Conference talk views: YouTube views of conference presentations?
- GitHub: Any open-source simulation environments or tools?
- Industry association membership and social presence?
""",

    Sector.GENERAL: """
SECTOR: Technology / Software

KEY SOCIAL SIGNALS:
- LinkedIn follower count and employee growth trend
- Twitter/X engagement rate relative to follower count
- Any notable community presence (Discord, Slack, Reddit)
- App store ratings if consumer-facing
- YouTube product demo engagement
""",
}


# ══════════════════════════════════════════════════════════════════════════════
#  Public accessor functions
# ══════════════════════════════════════════════════════════════════════════════

def get_team_context(sector: Sector) -> str:
    return TEAM_SECTOR_CONTEXT.get(sector, TEAM_SECTOR_CONTEXT[Sector.GENERAL])

def get_investor_context(sector: Sector) -> str:
    return INVESTOR_SECTOR_CONTEXT.get(sector, INVESTOR_SECTOR_CONTEXT[Sector.GENERAL])

def get_financials_context(sector: Sector) -> str:
    return FINANCIALS_SECTOR_CONTEXT.get(sector, FINANCIALS_SECTOR_CONTEXT[Sector.GENERAL])

def get_tech_context(sector: Sector) -> str:
    return TECH_SECTOR_CONTEXT.get(sector, TECH_SECTOR_CONTEXT[Sector.GENERAL])

def get_press_context(sector: Sector) -> str:
    return PRESS_SECTOR_CONTEXT.get(sector, PRESS_SECTOR_CONTEXT[Sector.GENERAL])

def get_social_context(sector: Sector) -> str:
    return SOCIAL_SECTOR_CONTEXT.get(sector, SOCIAL_SECTOR_CONTEXT[Sector.GENERAL])