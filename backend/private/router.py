from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_roles
from backend.database import engine, get_db
from backend.models import AuditSession, Role, User
from backend.schemas import AuditSessionRead, AuditSessionUpdate, UserCreate, UserRead, UserUpdate
from backend.public import OUTPUT_DIR, manifest_for_run, remove_run_directory
from backend.security import get_password_hash


router = APIRouter(prefix="/api/in", tags=["private"], dependencies=[Depends(get_current_user)])
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
def _sort_timestamp(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.get("/runs")
async def list_runs(db: Session = Depends(get_db)):
    items: list[AuditSessionRead] = []

    if inspect(engine).has_table("audit_sessions"):
        sessions = db.execute(
            select(AuditSession).order_by(AuditSession.created_at.desc(), AuditSession.id.desc())
        ).scalars().all()
        for session in sessions:
            run_path = OUTPUT_DIR / session.run_dir
            if not run_path.is_dir():
                continue
            items.append(_serialize_audit_session(session, manifest_for_run(run_path)))

    items.sort(key=lambda item: _sort_timestamp(item.created_at), reverse=True)
    return {"items": [item.model_dump() for item in items]}


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_audit_session(
    session_id: int,
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

    remove_run_directory(session_record.run_dir)
    db.delete(session_record)
    db.commit()


@router.get("/reports/{run_dir}")
async def list_private_run_reports(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = OUTPUT_DIR / run_dir
    if not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run directory not found")

    return {"run_dir": run_dir, "report_files": manifest_for_run(run_path)}


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
    report_files = manifest_for_run(run_path) if run_path.is_dir() else []
    return _serialize_audit_session(session_record, report_files)


@router.get("/reports/files/{relative_path:path}")
async def download_private_report_file(relative_path: str):
    from backend.public import download_report_file

    return await download_report_file(relative_path)


@router.get("/reports/{run_dir}/zip")
async def download_private_run_reports_zip(run_dir: str):
    from backend.public import download_run_reports_zip

    return await download_run_reports_zip(run_dir)


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