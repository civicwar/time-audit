import io
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_roles
from backend.database import engine, get_db
from backend.models import AuditSession, Role, User
from backend.schemas import AuditSessionRead, AuditSessionUpdate, UserCreate, UserRead, UserUpdate
from backend.security import get_password_hash
from time_audit import generate_time_audit


router = APIRouter(prefix="/api/in", tags=["private"], dependencies=[Depends(get_current_user)])

OUTPUT_DIR = Path("output")


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_relative_output_path(relative_path: str) -> Path:
    candidate = (OUTPUT_DIR / relative_path).resolve()
    output_root = OUTPUT_DIR.resolve()
    if output_root not in candidate.parents or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Report file not found.")
    return candidate


def _manifest_for_run(run_path: Path) -> list[dict]:
    manifest_path = run_path / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as file_obj:
            manifest = json.load(file_obj)
        return manifest.get("report_files", [])

    report_files = []
    for name in sorted(os.listdir(run_path)):
        if not name.endswith("_report.json"):
            continue
        user = name[:-12].replace("_", " ").strip().title()
        report_files.append(
            {
                "user": user,
                "filename": name,
                "relative_path": f"{run_path.name}/{name}",
            }
        )
    return report_files


def _parse_run_timestamp(run_dir: str) -> datetime | None:
    ts_part = run_dir.split("_")[0]
    try:
        return datetime.strptime(ts_part, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _serialize_audit_session(session: AuditSession, report_files: list[dict]) -> AuditSessionRead:
    return AuditSessionRead(
        id=session.id,
        name=session.name,
        run_dir=session.run_dir,
        report_files=report_files,
        source_type=session.source_type,
        created_at=session.created_at,
        created_by_username=session.created_by.username if session.created_by else None,
        clockify_workspace_name=session.clockify_workspace_name,
        start_date=session.start_date.isoformat() if session.start_date else None,
        end_date=session.end_date.isoformat() if session.end_date else None,
        timezone=session.timezone,
        big_task_hours=session.big_task_hours,
        is_legacy=False,
    )


def _serialize_legacy_run(run_dir: str, report_files: list[dict]) -> AuditSessionRead:
    return AuditSessionRead(
        run_dir=run_dir,
        report_files=report_files,
        source_type="legacy",
        created_at=_parse_run_timestamp(run_dir),
        is_legacy=True,
    )


def _sort_timestamp(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/runs")
async def list_runs(db: Session = Depends(get_db)):
    _ensure_output_dir()
    output_entries = {
        entry.name: entry for entry in OUTPUT_DIR.iterdir() if entry.is_dir()
    }

    items: list[AuditSessionRead] = []
    seen_run_dirs: set[str] = set()

    if inspect(engine).has_table("audit_sessions"):
        sessions = db.execute(
            select(AuditSession).order_by(AuditSession.created_at.desc(), AuditSession.id.desc())
        ).scalars().all()
        for session in sessions:
            run_path = output_entries.get(session.run_dir)
            if run_path is None:
                continue
            items.append(_serialize_audit_session(session, _manifest_for_run(run_path)))
            seen_run_dirs.add(session.run_dir)

    for run_dir, run_path in sorted(output_entries.items(), reverse=True):
        if run_dir in seen_run_dirs:
            continue
        items.append(_serialize_legacy_run(run_dir, _manifest_for_run(run_path)))

    items.sort(key=lambda item: _sort_timestamp(item.created_at), reverse=True)
    return {"items": [item.model_dump() for item in items]}


@router.post("/audit")
async def audit_csv(
    file: UploadFile = File(...),
    big_task_hours: float = 8.0,
    _: User = Depends(require_roles(Role.ADMIN, Role.DEVELOPER)),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    _ensure_output_dir()
    content = await file.read()
    try:
        results = generate_time_audit(
            csv_content=content.decode("utf-8"),
            big_task_hours=big_task_hours,
            output_dir=str(OUTPUT_DIR),
            write_reports=True,
            retention_hours=24,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Processing error: {exc}") from exc

    return results


@router.get("/reports/{run_dir}")
async def list_run_reports(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = OUTPUT_DIR / run_dir
    if not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run directory not found")

    return {"run_dir": run_dir, "report_files": _manifest_for_run(run_path)}


@router.get("/reports/{run_dir}/zip")
async def download_run_reports_zip(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = OUTPUT_DIR / run_dir
    if not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run directory not found")

    report_names = [
        name for name in sorted(os.listdir(run_path)) if name.endswith("_report.json")
    ]
    if not report_names:
        raise HTTPException(status_code=404, detail="No reports found for this run")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in report_names:
            archive.write(run_path / name, arcname=name)

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{run_dir}_reports.zip"'},
    )


@router.get("/reports/files/{relative_path:path}")
async def download_report_file(relative_path: str):
    if ".." in relative_path:
        raise HTTPException(status_code=400, detail="Invalid report path")

    file_path = _safe_relative_output_path(relative_path)
    return FileResponse(file_path, media_type="application/json", filename=file_path.name)


@router.patch("/sessions/{session_id}", response_model=AuditSessionRead)
async def update_audit_session(
    session_id: int,
    payload: AuditSessionUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
):
    if not inspect(engine).has_table("audit_sessions"):
        raise HTTPException(status_code=404, detail="Audit sessions are not available yet.")

    session_record = db.execute(
        select(AuditSession).where(AuditSession.id == session_id)
    ).scalar_one_or_none()
    if session_record is None:
        raise HTTPException(status_code=404, detail="Audit session not found.")

    normalized_name = payload.name.strip() if payload.name else None
    session_record.name = normalized_name or None
    db.add(session_record)
    db.commit()
    db.refresh(session_record)

    run_path = OUTPUT_DIR / session_record.run_dir
    report_files = _manifest_for_run(run_path) if run_path.is_dir() else []
    return _serialize_audit_session(session_record, report_files)


@router.get("/users", response_model=list[UserRead])
async def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
):
    users = db.execute(select(User).order_by(User.username.asc())).scalars().all()
    return [UserRead.model_validate(user) for user in users]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMIN)),
):
    existing = db.execute(select(User).where(User.username == payload.username)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists.")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(Role.ADMIN)),
):
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password:
        user.password_hash = get_password_hash(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        if user.id == current_user.id and not payload.is_active:
            raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")
        user.is_active = payload.is_active

    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user)