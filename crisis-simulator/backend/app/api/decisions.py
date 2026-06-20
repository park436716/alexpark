from fastapi import APIRouter
from pydantic import BaseModel

from app.services.evaluator import evaluate_user_decision

router = APIRouter()


class DecisionRequest(BaseModel):
    scenario: dict
    session: dict
    user_decision: str
    reference_cases: list


@router.post("/decisions/evaluate")
def evaluate_decision(request: DecisionRequest):
    return evaluate_user_decision(
        scenario=request.scenario,
        session=request.session,
        user_decision=request.user_decision,
        reference_cases=request.reference_cases,
    )
