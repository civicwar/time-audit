import io
import json
import os
import shutil
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from time_audit import generate_time_audit


router = APIRouter(tags=["public"])

OUTPUT_DIR = Path("output")


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_relative_output_path(relative_path: str) -> Path:
    candidate = (OUTPUT_DIR / relative_path).resolve()
    output_root = OUTPUT_DIR.resolve()
    if output_root not in candidate.parents or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Report file not found.")
    return candidate


def manifest_for_run(run_path: Path) -> list[dict]:
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


def remove_run_directory(run_dir: str) -> None:
    run_path = OUTPUT_DIR / run_dir
    if run_path.exists() and not run_path.is_dir():
        raise HTTPException(status_code=500, detail="Stored session path is invalid.")
    if run_path.is_dir():
        shutil.rmtree(run_path)


def build_reports_zip_response(run_path: Path, report_names: list[str], archive_name: str) -> Response:
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
        headers={"Content-Disposition": f'attachment; filename="{archive_name}"'},
    )


@router.post("/api/audit")
async def audit_csv(
    file: UploadFile = File(...),
    big_task_hours: float = 8.0,
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    ensure_output_dir()
    content = await file.read()
    try:
        return generate_time_audit(
            csv_content=content.decode("utf-8"),
            big_task_hours=big_task_hours,
            output_dir=str(OUTPUT_DIR),
            write_reports=True,
            retention_hours=24,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Processing error: {exc}") from exc


@router.get("/api/reports/{run_dir}")
async def list_run_reports(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = OUTPUT_DIR / run_dir
    if not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run directory not found")

    return {"run_dir": run_dir, "report_files": manifest_for_run(run_path)}


@router.get("/api/reports/{run_dir}/zip")
async def download_run_reports_zip(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = OUTPUT_DIR / run_dir
    if not run_path.is_dir():
        raise HTTPException(status_code=404, detail="Run directory not found")

    report_names = [
        name for name in sorted(os.listdir(run_path)) if name.endswith("_report.json")
    ]
    return build_reports_zip_response(run_path, report_names, f"{run_dir}_reports.zip")


@router.get("/api/reports/files/{relative_path:path}")
async def download_report_file(relative_path: str):
    if ".." in relative_path:
        raise HTTPException(status_code=400, detail="Invalid report path")

    file_path = safe_relative_output_path(relative_path)
    return FileResponse(file_path, media_type="application/json", filename=file_path.name)