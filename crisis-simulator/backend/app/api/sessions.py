import uuid
from typing import List, Optional

from fastapi import APIRouter

from app.config import INITIAL_SCORES
from app.services.scenario_generator import generate_static_scenario

router = APIRouter()


@router.post("/sessions/start")
def start_session(
    case_id: str,
    roles: Optional[List[str]] = None,
    workshop_id: Optional[str] = None,
    agency_id: Optional[str] = None,
    client_name: Optional[str] = None,
):
    scenario = generate_static_scenario(case_id)
    session = {
        "id": str(uuid.uuid4()),
        "user_id": "demo_user",
        "scenario_id": scenario["id"],
        "current_phase": "0h_detection",
        "current_context": scenario["initial_context"],
        "scores": dict(INITIAL_SCORES),
        "decision_history": [],
        "is_completed": False,
        "workshop_id": workshop_id,
        "agency_id": agency_id,
        "client_name": client_name,
        "roles": roles or [],
        "decisions_by_phase": {},
    }
    return {"scenario": scenario, "session": session}
