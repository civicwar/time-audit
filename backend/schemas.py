from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from backend.models import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: Role
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead


class AuditSessionRead(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    run_dir: str
    report_files: list[dict]
    source_type: str
    created_at: Optional[datetime] = None
    created_by_username: Optional[str] = None
    clockify_workspace_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    timezone: Optional[str] = None
    big_task_hours: Optional[float] = None
    time_stats: Optional[dict] = None
    overlap_per_user: Optional[dict] = None
    small_tasks_per_user: Optional[dict] = None
    big_tasks_per_user: Optional[dict] = None
    is_legacy: bool = False


class AuditSessionUpdate(BaseModel):
    name: Optional[str] = None


class ApplicationLogRead(BaseModel):
    available: bool = False
    path: str
    content: str = ""
    line_count: int = 0
    updated_at: Optional[datetime] = None
    size_bytes: int = 0