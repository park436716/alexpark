from app.config import PHASES


def get_next_phase(current_phase: str) -> str:
    try:
        index = PHASES.index(current_phase)
        return PHASES[index + 1]
    except (ValueError, IndexError):
        return "completed"
