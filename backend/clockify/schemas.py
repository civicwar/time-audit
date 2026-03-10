from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ClockifyAuditRequest(BaseModel):
    start_date: date
    end_date: date
    timezone: str = Field(min_length=1, max_length=128)
    big_task_hours: float = Field(default=8.0, ge=0)
    session_name: Optional[str] = Field(default=None, max_length=255)


class ClockifyProfileResponse(BaseModel):
    configured: bool
    workspace_id: str | None = None
    workspace_name: str | None = None
    user_name: str | None = None
    default_timezone: str | None = None