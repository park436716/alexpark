import uuid

_SCENARIOS = {
    "united_like": {
        "id": str(uuid.uuid4()),
        "title": "Viral Passenger Removal Crisis",
        "industry": "airline",
        "crisis_type": "customer_abuse",
        "reference_cases": ["united_2017"],
        "initial_context": (
            "A passenger removal video is spreading rapidly on X and TikTok. "
            "The video has 4.5 million views within two hours. "
            "The passenger appears injured. "
            "Reporters are asking for an official statement. "
            "Employees internally claim they followed policy."
        ),
        "stakeholders": [
            "injured passenger",
            "customers",
            "employees",
            "media",
            "regulators",
            "investors",
        ],
        "difficulty": "medium",
        "time_horizon": [
            "0h_detection",
            "2h_initial_response",
            "6h_media_escalation",
            "24h_regulatory_attention",
            "72h_internal_accountability",
            "7d_recovery_plan",
        ],
    },
}


def generate_static_scenario(case_id: str) -> dict:
    if case_id not in _SCENARIOS:
        raise KeyError(f"Unknown scenario case_id: {case_id}")
    return _SCENARIOS[case_id]
