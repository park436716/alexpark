from typing import Optional

from pydantic import BaseModel


class UserDecision(BaseModel):
    session_id: str
    phase: str
    role: str
    decision_text: str
    selected_option: Optional[str] = None
