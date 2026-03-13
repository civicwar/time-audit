from datetime import date, datetime

from sqlalchemy.orm import Session

from backend.clockify.client import ClockifyClient, ClockifyClientError, ClockifyConfigurationError
from backend.models import AuditSession, AuditSessionTimeEntry
from time_audit import generate_time_audit


def serialize_session_reference(session: AuditSession) -> dict:
    return {
        "id": session.id,
        "name": session.name,
        "run_dir": session.run_dir,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


def _parse_report_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def _build_time_entry_rows(report_by_user_by_date: dict) -> list[AuditSessionTimeEntry]:
    time_entries: list[AuditSessionTimeEntry] = []
    for user_name, dates in (report_by_user_by_date or {}).items():
        for items in (dates or {}).values():
            for item in items or []:
                start_raw = item.get("start_datetime")
                end_raw = item.get("end_datetime")
                duration_hours = item.get("duration")
                if not start_raw or not end_raw or duration_hours is None:
                    continue

                time_entries.append(
                    AuditSessionTimeEntry(
                        user_name=user_name,
                        description=item.get("description") or "",
                        start_datetime=_parse_report_datetime(start_raw),
                        end_datetime=_parse_report_datetime(end_raw),
                        duration_hours=float(duration_hours),
                    )
                )

    time_entries.sort(key=lambda entry: (entry.user_name, entry.start_datetime, entry.end_datetime, entry.description))
    return time_entries


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
        run_dir_name=existing_session.run_dir if existing_session is not None else None,
        write_reports=True,
        retention_hours=24,
    )

    run_dir = results.get("run_dir")
    if not run_dir:
        raise RuntimeError("Audit completed without a run directory.")

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
            time_stats=results.get("time_stats"),
            overlap_per_user=results.get("overlap_per_user"),
            small_tasks_per_user=results.get("small_tasks_per_user"),
            big_tasks_per_user=results.get("big_tasks_per_user"),
            created_by_user_id=created_by_user_id,
        )
    else:
        audit_session = existing_session
        audit_session.run_dir = run_dir
        audit_session.source_type = "clockify"
        audit_session.clockify_workspace_id = profile.workspace_id
        audit_session.clockify_workspace_name = profile.workspace_name
        audit_session.start_date = start_date
        audit_session.end_date = end_date
        audit_session.timezone = timezone_name
        audit_session.big_task_hours = big_task_hours
        audit_session.time_stats = results.get("time_stats")
        audit_session.overlap_per_user = results.get("overlap_per_user")
        audit_session.small_tasks_per_user = results.get("small_tasks_per_user")
        audit_session.big_tasks_per_user = results.get("big_tasks_per_user")
        if session_name is not None:
            audit_session.name = session_name or None

    audit_session.time_entries = _build_time_entry_rows(results.get("report_by_user_by_date") or {})

    db.add(audit_session)
    db.commit()
    db.refresh(audit_session)

    results["session"] = serialize_session_reference(audit_session)
    return results, audit_session