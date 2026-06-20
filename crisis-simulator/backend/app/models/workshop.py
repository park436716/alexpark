from typing import List, Optional

from pydantic import BaseModel


class Agency(BaseModel):
    id: str
    name: str
    logo_url: Optional[str] = None
    report_template: Optional[str] = None  # branding hook for PDF export


class Workshop(BaseModel):
    id: str
    agency_id: str
    client_name: str
    scenario_id: str
    roles: List[str]
    facilitator_user_id: str
    is_active: bool = True
