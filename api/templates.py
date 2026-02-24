"""Industry templates for onboarding wizard."""

TEMPLATES = {
    "restaurant": {
        "display_name": "Restaurant / Food Service",
        "industry": "restaurant",
        "fields": [
            {"name": "restaurant_size", "type": "enum", "options": ["small", "medium", "large", "enterprise"], "description": "Number of locations or seats"},
            {"name": "restaurant_type", "type": "enum", "options": ["fast_casual", "fine_dining", "qsr", "bar_nightclub", "cafe", "food_truck", "catering", "ghost_kitchen"], "description": "Type of restaurant operation"},
            {"name": "location_count", "type": "integer", "description": "Number of locations the prospect operates"},
            {"name": "current_pos", "type": "text", "description": "Current POS system they're using"},
            {"name": "pain_points", "type": "list", "description": "Specific pain points mentioned", "examples": ["staff_scheduling", "inventory_waste", "slow_checkout", "reporting_gaps"]},
            {"name": "competitor_mentions", "type": "list", "description": "Other systems mentioned"},
            {"name": "buying_stage", "type": "enum", "options": ["early_research", "evaluating", "decision_ready", "negotiating"], "description": "Where they are in the buying process"},
        ],
    },
    "saas": {
        "display_name": "SaaS Sales",
        "industry": "saas",
        "fields": [
            {"name": "company_size", "type": "enum", "options": ["startup", "smb", "mid_market", "enterprise"], "description": "Size of the prospect company"},
            {"name": "current_tools", "type": "list", "description": "Tools/software they currently use", "examples": ["salesforce", "hubspot", "slack", "jira"]},
            {"name": "use_case", "type": "text", "description": "Primary use case or problem they're solving"},
            {"name": "contract_value", "type": "text", "description": "Estimated deal size or budget"},
            {"name": "pain_points", "type": "list", "description": "Specific pain points mentioned"},
            {"name": "competitor_mentions", "type": "list", "description": "Other solutions mentioned"},
            {"name": "decision_timeline", "type": "text", "description": "When they plan to make a decision"},
            {"name": "buying_stage", "type": "enum", "options": ["early_research", "evaluating", "decision_ready", "negotiating"], "description": "Where they are in the buying process"},
        ],
    },
    "real_estate": {
        "display_name": "Real Estate",
        "industry": "real_estate",
        "fields": [
            {"name": "property_type", "type": "enum", "options": ["residential", "commercial", "industrial", "mixed_use", "land"], "description": "Type of property"},
            {"name": "budget_range", "type": "text", "description": "Budget or price range mentioned"},
            {"name": "timeline", "type": "text", "description": "When they want to buy/sell/lease"},
            {"name": "location_preference", "type": "text", "description": "Preferred area or neighborhood"},
            {"name": "financing_status", "type": "enum", "options": ["pre_approved", "exploring", "cash_buyer", "unknown"], "description": "Financing situation"},
            {"name": "pain_points", "type": "list", "description": "Concerns or challenges mentioned"},
            {"name": "competitor_mentions", "type": "list", "description": "Other agents or platforms mentioned"},
        ],
    },
    "healthcare": {
        "display_name": "Healthcare",
        "industry": "healthcare",
        "fields": [
            {"name": "practice_size", "type": "enum", "options": ["solo", "small_group", "large_group", "hospital_system"], "description": "Size of the practice or facility"},
            {"name": "specialty", "type": "text", "description": "Medical specialty"},
            {"name": "current_ehr", "type": "text", "description": "Current EHR/EMR system"},
            {"name": "compliance_concerns", "type": "list", "description": "Regulatory or compliance issues mentioned", "examples": ["hipaa", "interoperability", "billing_codes"]},
            {"name": "pain_points", "type": "list", "description": "Specific pain points mentioned"},
            {"name": "patient_volume", "type": "text", "description": "Number of patients or visits"},
            {"name": "buying_stage", "type": "enum", "options": ["early_research", "evaluating", "decision_ready", "negotiating"], "description": "Where they are in the buying process"},
        ],
    },
    "general": {
        "display_name": "General Sales",
        "industry": "general",
        "fields": [
            {"name": "pain_points", "type": "list", "description": "Specific pain points mentioned"},
            {"name": "competitor_mentions", "type": "list", "description": "Other solutions mentioned"},
            {"name": "buying_stage", "type": "enum", "options": ["early_research", "evaluating", "decision_ready", "negotiating"], "description": "Where they are in the buying process"},
            {"name": "decision_maker", "type": "boolean", "description": "Is the person on the call the decision maker?"},
            {"name": "budget_mentioned", "type": "boolean", "description": "Was a budget discussed?"},
            {"name": "timeline", "type": "text", "description": "When they want to make a decision"},
        ],
    },
}


def get_template(industry: str) -> dict:
    """Get a template by industry key."""
    return TEMPLATES.get(industry, TEMPLATES["general"])


def list_templates() -> list:
    """List all available templates."""
    return [
        {"key": key, "display_name": t["display_name"], "industry": t["industry"], "field_count": len(t["fields"])}
        for key, t in TEMPLATES.items()
    ]
