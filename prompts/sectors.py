"""
prompts/sectors.py — Sector detection for context-aware agent prompts.

After the seed crawler identifies the company's industry,
detect_sector() maps it to one of our supported sectors.
Each sector unlocks different research signals and metrics
in every specialist agent's prompt.
"""

from enum import Enum


class Sector(str, Enum):
    AI_TECH        = "ai_tech"          # AI, ML, Developer Tools, Cloud
    FINTECH        = "fintech"          # Payments, Banking, Insurance, Crypto
    HEALTHCARE     = "healthcare"       # Healthtech, Biotech, Pharma, MedDevice
    SAAS_ENTERPRISE= "saas_enterprise"  # B2B SaaS, Enterprise Software, CRM
    ECOMMERCE      = "ecommerce"        # E-commerce, D2C, Marketplaces, Retail
    CONSUMER       = "consumer"         # B2C Apps, Social, Gaming, Media
    DEEPTECH       = "deeptech"         # Robotics, Hardware, Space, CleanTech
    GENERAL        = "general"          # Fallback for unrecognized sectors


# Keywords that map to each sector
# The detector checks the company's industry/description against these
_SECTOR_KEYWORDS: dict[Sector, list[str]] = {
    Sector.AI_TECH: [
        "artificial intelligence", "machine learning", "deep learning",
        "nlp", "computer vision", "llm", "foundation model", "mlops",
        "developer tools", "developer platform", "cloud infrastructure",
        "data platform", "analytics platform", "open source ai",
        "hugging face", "transformers", "diffusion", "generative ai",
        "api platform", "model deployment", "vector database",
    ],
    Sector.FINTECH: [
        "fintech", "financial technology", "payments", "banking",
        "neobank", "digital bank", "insurance", "insurtech", "lending",
        "credit", "mortgage", "wealth management", "trading", "crypto",
        "blockchain", "defi", "remittance", "payroll", "accounting",
        "tax", "invoice", "treasury", "regtech", "compliance",
    ],
    Sector.HEALTHCARE: [
        "healthcare", "health tech", "healthtech", "biotech", "biotechnology",
        "pharmaceutical", "pharma", "medical device", "medtech", "clinical",
        "telemedicine", "telehealth", "mental health", "diagnostics",
        "drug discovery", "genomics", "digital health", "ehr", "emr",
        "hospital", "patient", "clinical trial", "fda", "life sciences",
    ],
    Sector.SAAS_ENTERPRISE: [
        "saas", "software as a service", "enterprise software", "b2b software",
        "crm", "erp", "hrm", "hris", "project management", "collaboration",
        "workflow automation", "business intelligence", "data analytics",
        "cybersecurity", "security platform", "devops", "ci/cd", "monitoring",
        "observability", "identity", "access management", "procurement",
    ],
    Sector.ECOMMERCE: [
        "e-commerce", "ecommerce", "marketplace", "retail", "d2c",
        "direct to consumer", "shopify", "logistics", "supply chain",
        "fulfillment", "dropshipping", "fashion", "apparel", "food delivery",
        "grocery", "quick commerce", "resale", "recommerce",
    ],
    Sector.CONSUMER: [
        "consumer app", "social media", "social network", "gaming",
        "mobile app", "entertainment", "media", "streaming", "music",
        "podcast", "news", "content creation", "creator economy",
        "fitness", "education", "edtech", "learning", "dating", "travel",
    ],
    Sector.DEEPTECH: [
        "robotics", "hardware", "semiconductor", "chip", "space",
        "aerospace", "clean tech", "cleantech", "climate tech", "climatetech",
        "energy", "solar", "battery", "electric vehicle", "ev",
        "quantum", "nanotechnology", "materials science", "3d printing",
        "augmented reality", "virtual reality", "ar", "vr", "xr",
    ],
}


def detect_sector(seed_data: dict) -> Sector:
    """
    Detect the company's sector from seed crawler output.

    Checks industry field + description + products against keyword lists.
    Returns the best matching Sector enum value.

    Args:
        seed_data: The dict from seed_crawler (company_profile.json)

    Returns:
        Sector enum value (falls back to Sector.GENERAL if no match)
    """
    # Build a combined text blob from all relevant seed fields
    text_blob = " ".join([
        str(seed_data.get("industry", "")),
        str(seed_data.get("description", "")),
        str(seed_data.get("tagline", "")),
        str(seed_data.get("business_model", "")),
        " ".join(seed_data.get("products_services", [])),
        str(seed_data.get("company_name", "")),
    ]).lower()

    # Score each sector by keyword matches
    scores: dict[Sector, int] = {s: 0 for s in Sector}

    for sector, keywords in _SECTOR_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_blob:
                scores[sector] += 1

    # Find best match
    best_sector = max(scores, key=lambda s: scores[s])
    best_score = scores[best_sector]

    if best_score == 0:
        return Sector.GENERAL

    detected = best_sector
    print(f"  🏷️  Detected sector: [{detected.value}] (score: {best_score})")
    return detected


def get_sector_label(sector: Sector) -> str:
    """Human-readable sector label for use in prompts."""
    labels = {
        Sector.AI_TECH:         "Artificial Intelligence / Developer Tools / Cloud Infrastructure",
        Sector.FINTECH:         "Financial Technology / Payments / Banking / Insurance",
        Sector.HEALTHCARE:      "Healthcare / Biotech / Pharmaceutical / Medical Technology",
        Sector.SAAS_ENTERPRISE: "B2B SaaS / Enterprise Software / Cybersecurity",
        Sector.ECOMMERCE:       "E-commerce / Marketplace / Retail / Logistics",
        Sector.CONSUMER:        "Consumer Apps / Social / Gaming / Media / EdTech",
        Sector.DEEPTECH:        "Deep Tech / Robotics / Hardware / CleanTech / Space",
        Sector.GENERAL:         "Technology / Software",
    }
    return labels.get(sector, "Technology")