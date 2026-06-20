def apply_score_delta(current_scores: dict, evaluation: dict) -> dict:
    updated = current_scores.copy()
    delta_map = {
        "reputation": evaluation.get("reputation_delta", 0),
        "legal_risk": evaluation.get("legal_risk_delta", 0),
        "media_pressure": evaluation.get("media_pressure_delta", 0),
        "employee_trust": evaluation.get("employee_trust_delta", 0),
        "regulatory_risk": evaluation.get("regulatory_risk_delta", 0),
        "financial_risk": evaluation.get("financial_risk_delta", 0),
    }
    for key, delta in delta_map.items():
        current_value = updated.get(key, 50)
        updated[key] = max(0, min(100, current_value + delta))
    return updated
