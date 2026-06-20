from app.models.decision import UserDecision


def submit_role_decision(session: dict, decision: dict) -> dict:
    """Record one role's decision for the current phase without scoring yet.

    Scoring (the LLM evaluator call) only happens once every required role
    has submitted for the phase, or the facilitator forces an advance — see
    phase_is_complete() and app/api/facilitator.py.
    """
    phase = session["current_phase"]
    by_phase = session.setdefault("decisions_by_phase", {})
    phase_decisions = by_phase.setdefault(phase, {})
    phase_decisions[decision["role"]] = decision
    return session


def phase_is_complete(session: dict) -> bool:
    phase = session["current_phase"]
    required_roles = set(session.get("roles", []))
    if not required_roles:
        return True
    submitted_roles = set(session.get("decisions_by_phase", {}).get(phase, {}).keys())
    return required_roles.issubset(submitted_roles)

def phase_submission_status(session: dict) -> dict:
    phase = session["current_phase"]
    required_roles = session.get("roles", [])
    submitted = session.get("decisions_by_phase", {}).get(phase, {})
    return {
        "phase": phase,
        "submitted_roles": list(submitted.keys()),
        "pending_roles": [r for r in required_roles if r not in submitted],
        "is_complete": phase_is_complete(session),
    }


def combine_role_decisions_text(session: dict) -> str:
    """Flatten the current phase's per-role decisions into one text block
    for the evaluator, so the LLM can judge cross-role coherence (e.g. did
    Legal's "no comment" contradict PR's public apology)."""
    phase = session["current_phase"]
    phase_decisions = session.get("decisions_by_phase", {}).get(phase, {})
    lines = []
    for role, decision in phase_decisions.items():
        lines.append(f"[{role}]: {decision['decision_text']}")
    return "\n".join(lines)
