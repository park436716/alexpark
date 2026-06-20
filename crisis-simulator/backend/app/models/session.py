from typing import Dict, List

from pydantic import BaseModel


class CrisisSession(BaseModel):
    id: str
    user_id: str
    scenario_id: str
    current_phase: str
    current_context: str
    scores: Dict[str, int]
    decision_history: List[str]
    is_completed: bool = False
