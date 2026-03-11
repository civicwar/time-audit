from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_roles
from backend.clockify.client import ClockifyClient, ClockifyClientError, ClockifyConfigurationError
from backend.clockify.schemas import ClockifyAuditRequest, ClockifyProfileResponse
from backend.clockify.service import execute_clockify_audit
from backend.database import get_db
from backend.models import Role, User


router = APIRouter(prefix="/api/in/clockify", tags=["clockify"], dependencies=[Depends(get_current_user)])


@router.get("/profile", response_model=ClockifyProfileResponse)
async def get_clockify_profile(_: User = Depends(require_roles(Role.ADMIN))) -> ClockifyProfileResponse:
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN)),
):
    normalized_session_name = payload.session_name.strip() if payload.session_name else None
    if normalized_session_name and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can name sessions.")

    try:
        results, _ = await execute_clockify_audit(
            db=db,
            start_date=payload.start_date,
            end_date=payload.end_date,
            timezone_name=payload.timezone,
            big_task_hours=payload.big_task_hours,
            created_by_user_id=current_user.id,
            session_name=normalized_session_name,
        )
    except ClockifyConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ClockifyClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Processing error: {exc}") from exc

    return results