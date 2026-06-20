import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("CRISIS_SIM_MODEL", "gpt-4o")

INITIAL_SCORES = {
    "reputation": 70,
    "legal_risk": 30,
    "media_pressure": 40,
    "employee_trust": 60,
    "regulatory_risk": 30,
    "financial_risk": 25,
}

PHASES = [
    "0h_detection",
    "2h_initial_response",
    "6h_media_escalation",
    "24h_regulatory_attention",
    "72h_internal_accountability",
    "7d_recovery_plan",
    "30d_debrief",
]
