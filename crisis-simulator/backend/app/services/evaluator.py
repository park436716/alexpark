from app.llm.openai_client import evaluate_decision_with_llm
from app.services.scoring_engine import apply_score_delta
from app.services.state_machine import get_next_phase


def evaluate_user_decision(
    scenario: dict,
    session: dict,
    user_decision: str,
    reference_cases: list,
) -> dict:
    evaluation = evaluate_decision_with_llm(
        scenario=scenario,
        session=session,
        user_decision=user_decision,
        reference_cases=reference_cases,
    )

    updated_scores = apply_score_delta(
        current_scores=session["scores"],
        evaluation=evaluation,
    )

    next_phase = get_next_phase(session["current_phase"])

    updated_session = {
        **session,
        "current_phase": next_phase,
        "current_context": evaluation["next_context"],
        "scores": updated_scores,
        "decision_history": session["decision_history"] + [user_decision],
        "is_completed": next_phase == "completed",
    }

    return {
        "evaluation": evaluation,
        "updated_session": updated_session,
    }
