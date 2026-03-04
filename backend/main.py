from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from time_audit import generate_time_audit
from fastapi.responses import FileResponse
from starlette.responses import Response

import os
import json
import io
import zipfile

app = FastAPI(title="Time Audit API")

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = "output"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=OUTPUT_DIR), name="reports")


@app.post("/api/audit")
async def audit_csv(file: UploadFile = File(...), big_task_hours: float = 8.0):
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    content = await file.read()
    try:
        results = generate_time_audit(
            csv_content=content.decode("utf-8"),
            big_task_hours=big_task_hours,
            output_dir=OUTPUT_DIR,
            write_reports=True,
            retention_hours=24,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Processing error: {e}")

    return results


@app.options("/api/audit")
async def audit_options():  # explicit CORS preflight handler
    return Response(status_code=200)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/reports/{run_dir}/zip")
async def download_run_reports_zip(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = os.path.join(OUTPUT_DIR, run_dir)
    if not os.path.isdir(run_path):
        raise HTTPException(status_code=404, detail="Run directory not found")

    report_names = [
        name for name in sorted(os.listdir(run_path))
        if name.endswith("_report.json")
    ]
    if not report_names:
        raise HTTPException(status_code=404, detail="No reports found for this run")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in report_names:
            file_path = os.path.join(run_path, name)
            archive.write(file_path, arcname=name)

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{run_dir}_reports.zip"'
        },
    )


@app.get("/api/reports/{run_dir}")
async def list_run_reports(run_dir: str):
    if "/" in run_dir or ".." in run_dir:
        raise HTTPException(status_code=400, detail="Invalid run directory")

    run_path = os.path.join(OUTPUT_DIR, run_dir)
    if not os.path.isdir(run_path):
        raise HTTPException(status_code=404, detail="Run directory not found")

    manifest_path = os.path.join(run_path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
        return {"run_dir": run_dir, "report_files": manifest.get("report_files", [])}

    report_files = []
    for name in sorted(os.listdir(run_path)):
        if not name.endswith("_report.json"):
            continue
        user = name[:-12].replace("_", " ").strip().title()
        report_files.append({
            "user": user,
            "filename": name,
            "relative_path": f"{run_dir}/{name}",
        })

    return {"run_dir": run_dir, "report_files": report_files}

# Mount frontend last to avoid overshadowing /api routes
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):  # pragma: no cover
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return Response(status_code=404)
