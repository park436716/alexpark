import uuid

from fastapi import APIRouter

from app.config import INITIAL_SCORES
from app.services.scenario_generator import generate_static_scenario

router = APIRouter()


@router.post("/sessions/start")
def start_session(case_id: str):
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
    }
    return {"scenario": scenario, "session": session}
