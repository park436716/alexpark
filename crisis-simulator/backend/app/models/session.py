from typing import Dict, List, Optional

from pydantic import BaseModel

from app.models.decision import UserDecision


class CrisisSession(BaseModel):
    id: str
    user_id: str
    scenario_id: str
    current_phase: str
    current_context: str
    scores: Dict[str, int]
    decision_history: List[str]
    is_completed: bool = False

    # --- B2B workshop fields (multi-role facilitated sessions) ---
    workshop_id: Optional[str] = None
    agency_id: Optional[str] = None
    client_name: Optional[str] = None
    roles: List[str] = []
    # current_phase -> { role -> decision }; a phase only scores once
    # every required role has submitted, or the facilitator forces it.
    decisions_by_phase: Dict[str, Dict[str, UserDecision]] = {}
