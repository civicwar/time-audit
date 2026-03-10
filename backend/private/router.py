import io
import json
import os
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import get_current_user, require_roles
from backend.database import get_db
from backend.models import Role, User
from backend.schemas import UserCreate, UserRead, UserUpdate
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


@router.get("/runs")
async def list_runs():
    _ensure_output_dir()
    items = []
    for entry in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        items.append(
            {
                "run_dir": entry.name,
                "report_files": _manifest_for_run(entry),
            }
        )
    return {"items": items}


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