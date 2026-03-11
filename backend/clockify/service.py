from datetime import date

from sqlalchemy.orm import Session

from backend.clockify.client import ClockifyClient, ClockifyClientError, ClockifyConfigurationError
from backend.models import AuditSession
from backend.public import remove_run_directory
from time_audit import generate_time_audit


def serialize_session_reference(session: AuditSession) -> dict:
    return {
        "id": session.id,
        "name": session.name,
        "run_dir": session.run_dir,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


async def execute_clockify_audit(
    *,
    db: Session,
    start_date: date,
    end_date: date,
    timezone_name: str,
    big_task_hours: float,
    created_by_user_id: int | None = None,
    session_name: str | None = None,
    existing_session: AuditSession | None = None,
) -> tuple[dict, AuditSession]:
    client = ClockifyClient()
    profile = await client.get_profile()
    csv_content = await client.fetch_detailed_report_csv(
        start_date=start_date,
        end_date=end_date,
        timezone_name=timezone_name,
    )

    results = generate_time_audit(
        csv_content=csv_content,
        big_task_hours=big_task_hours,
        output_dir="output",
        write_reports=True,
        retention_hours=24,
    )

    run_dir = results.get("run_dir")
    if not run_dir:
        raise RuntimeError("Audit completed without a run directory.")

    previous_run_dir = None
    if existing_session is None:
        if created_by_user_id is None:
            raise RuntimeError("A creator is required when persisting a new session.")

        audit_session = AuditSession(
            name=session_name or None,
            run_dir=run_dir,
            source_type="clockify",
            clockify_workspace_id=profile.workspace_id,
            clockify_workspace_name=profile.workspace_name,
            start_date=start_date,
            end_date=end_date,
            timezone=timezone_name,
            big_task_hours=big_task_hours,
            created_by_user_id=created_by_user_id,
        )
    else:
        audit_session = existing_session
        previous_run_dir = existing_session.run_dir
        audit_session.run_dir = run_dir
        audit_session.source_type = "clockify"
        audit_session.clockify_workspace_id = profile.workspace_id
        audit_session.clockify_workspace_name = profile.workspace_name
        audit_session.start_date = start_date
        audit_session.end_date = end_date
        audit_session.timezone = timezone_name
        audit_session.big_task_hours = big_task_hours
        if session_name is not None:
            audit_session.name = session_name or None

    db.add(audit_session)
    db.commit()
    db.refresh(audit_session)

    if previous_run_dir and previous_run_dir != audit_session.run_dir:
        remove_run_directory(previous_run_dir)

    results["session"] = serialize_session_reference(audit_session)
    return results, audit_session