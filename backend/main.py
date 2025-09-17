from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from time_audit import generate_time_audit

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

# Mount static reports (will be ensured later in startup if missing)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=OUTPUT_DIR), name="reports")


@app.post("/api/audit")
async def audit_csv(file: UploadFile = File(...), big_task_hours: float = 8.0):
    if not file.filename.endswith('.csv'):
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


@app.get("/api/health")
async def health():
    return {"status": "ok"}
