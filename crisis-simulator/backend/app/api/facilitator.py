from fastapi import APIRouter
from pydantic import BaseModel

from app.services.evaluator import evaluate_user_decision
from app.services.workshop_session import (
    combine_role_decisions_text,
    phase_is_complete,
    phase_submission_status,
    submit_role_decision,
)

router = APIRouter()


class RoleDecisionRequest(BaseModel):
    session: dict
    role: str
    decision_text: str


class AdvancePhaseRequest(BaseModel):
    scenario: dict
    session: dict
    reference_cases: list


@router.post("/facilitator/submit")
def submit_decision(request: RoleDecisionRequest):
    session = submit_role_decision(
        request.session,
        {"role": request.role, "decision_text": request.decision_text},
    )
    return {"session": session, "status": phase_submission_status(session)}


@router.post("/facilitator/status")
def get_status(session: dict):
    return phase_submission_status(session)


@router.post("/facilitator/advance")
def force_advance_phase(request: AdvancePhaseRequest):
    """Score the current phase now, even if not every role has submitted.

    Used by the facilitator console's manual override button — real
    workshops run on a clock, not on waiting for the slowest role.
    """
    combined_text = combine_role_decisions_text(request.session)
    return evaluate_user_decision(
        scenario=request.scenario,
        session=request.session,
        user_decision=combined_text,
        reference_cases=request.reference_cases,
    )
