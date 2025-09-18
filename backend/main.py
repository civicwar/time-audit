from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from time_audit import generate_time_audit
from fastapi.responses import FileResponse
from starlette.responses import Response

import os

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
