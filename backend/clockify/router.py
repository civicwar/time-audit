from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth import get_current_user, require_roles
from backend.clockify.client import ClockifyClient, ClockifyClientError, ClockifyConfigurationError
from backend.clockify.schemas import ClockifyAuditRequest, ClockifyProfileResponse
from backend.models import Role, User
from time_audit import generate_time_audit


router = APIRouter(prefix="/api/in/clockify", tags=["clockify"], dependencies=[Depends(get_current_user)])


@router.get("/profile", response_model=ClockifyProfileResponse)
async def get_clockify_profile() -> ClockifyProfileResponse:
    try:
        profile = await ClockifyClient().get_profile()
    except ClockifyConfigurationError:
        return ClockifyProfileResponse(configured=False)
    except ClockifyClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return ClockifyProfileResponse(
        configured=True,
        workspace_id=profile.workspace_id,
        workspace_name=profile.workspace_name,
        user_name=profile.user_name,
        default_timezone=profile.default_timezone,
    )


@router.post("/audit")
async def audit_from_clockify(
    payload: ClockifyAuditRequest,
    _: User = Depends(require_roles(Role.ADMIN, Role.DEVELOPER)),
):
    try:
        csv_content = await ClockifyClient().fetch_detailed_report_csv(
            start_date=payload.start_date,
            end_date=payload.end_date,
            timezone_name=payload.timezone,
        )
    except ClockifyConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ClockifyClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        return generate_time_audit(
            csv_content=csv_content,
            big_task_hours=payload.big_task_hours,
            output_dir="output",
            write_reports=True,
            retention_hours=24,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Processing error: {exc}") from exc