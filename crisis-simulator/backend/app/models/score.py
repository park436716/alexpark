from typing import Dict, List

from pydantic import BaseModel


class EvaluationResult(BaseModel):
    decision_quality: int
    reputation_delta: int
    legal_risk_delta: int
    media_pressure_delta: int
    employee_trust_delta: int
    regulatory_risk_delta: int
    financial_risk_delta: int
    strengths: List[str]
    weaknesses: List[str]
    next_context: str
    stakeholder_reactions: Dict[str, str]
    recommended_next_action: str
