from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_roles
from backend.clockify.client import ClockifyClient, ClockifyClientError, ClockifyConfigurationError
from backend.clockify.schemas import ClockifyAuditRequest, ClockifyProfileResponse
from backend.database import get_db
from backend.models import AuditSession, Role, User
from time_audit import generate_time_audit


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
        client = ClockifyClient()
        profile = await client.get_profile()
        csv_content = await client.fetch_detailed_report_csv(
            start_date=payload.start_date,
            end_date=payload.end_date,
            timezone_name=payload.timezone,
        )
    except ClockifyConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ClockifyClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        results = generate_time_audit(
            csv_content=csv_content,
            big_task_hours=payload.big_task_hours,
            output_dir="output",
            write_reports=True,
            retention_hours=24,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Processing error: {exc}") from exc

    run_dir = results.get("run_dir")
    if not run_dir:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Audit completed without a run directory.")

    audit_session = AuditSession(
        name=normalized_session_name or None,
        run_dir=run_dir,
        source_type="clockify",
        clockify_workspace_id=profile.workspace_id,
        clockify_workspace_name=profile.workspace_name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        timezone=payload.timezone,
        big_task_hours=payload.big_task_hours,
        created_by_user_id=current_user.id,
    )
    db.add(audit_session)
    db.commit()
    db.refresh(audit_session)

    results["session"] = {
        "id": audit_session.id,
        "name": audit_session.name,
        "run_dir": audit_session.run_dir,
        "created_at": audit_session.created_at.isoformat() if audit_session.created_at else None,
    }
    return results