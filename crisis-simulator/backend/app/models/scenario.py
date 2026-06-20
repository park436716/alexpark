from typing import List, Literal

from pydantic import BaseModel


class Scenario(BaseModel):
    id: str
    title: str
    industry: str
    crisis_type: Literal[
        "product_safety",
        "customer_abuse",
        "data_breach",
        "executive_misconduct",
        "labor_issue",
        "racial_bias",
        "operational_failure",
        "financial_misconduct",
        "ai_failure",
    ]
    reference_cases: List[str]
    initial_context: str
    stakeholders: List[str]
    difficulty: Literal["easy", "medium", "hard", "expert"]
    time_horizon: List[str]
