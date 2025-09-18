## Time Audit

Python utilities to analyze Clockify detailed report exports.

### Library Usage

Import and call `generate_time_audit` with the raw CSV content string.

```python
from time_audit import generate_time_audit

with open("report.csv", "r", encoding="utf-8") as f:
	csv_content = f.read()

results = generate_time_audit(csv_content, big_task_hours=8.0, output_dir="output")

print(results["time_stats"])  # {'total_time': ..., 'time_per_user': {...}}
```

Returned dictionary keys:
- `overlap_per_user`
- `time_stats`
- `small_tasks_per_user`
- `big_tasks_per_user`
- `report_by_user_by_date`
- `big_task_hours`
- `report_files` (list of objects `{user, filename}` for the current run; empty list if `write_reports=False`)

Report writing behavior (per-request isolation):
- When `write_reports=True`, per-user JSON files are written (grouped by date) into a unique run subdirectory under `output/`.
- Each run directory name: `YYYYMMDDTHHMMSSZ_<rand6>` (UTC timestamp + short random suffix).
- Inside the run directory filenames follow `<user>_report.json`.
- The function returns `run_dir` plus `report_files` containing `relative_path` so clients can build download URLs.
- Directories older than the configured retention (default 24 hours) are automatically deleted.
- The previous `clean_output_dir` parameter is deprecated and ignored (kept only for backward compatibility).

### CLI Wrapper

Running the repository directly (or `python main.py`) expects a `report.csv` in the working directory and will output summaries and JSON reports in `./output`.

```bash
python main.py
```

### Future Web Integration

The refactored function signature is:

```python
generate_time_audit(
	csv_content: str,
	big_task_hours: float = 8.0,
	output_dir: str | None = None,
	write_reports: bool = True,
	clean_output_dir: bool = False,  # deprecated
	retention_hours: int = 24,
) -> dict
```

This allows easy integration into a web endpoint that accepts an uploaded CSV and returns JSON.

### Web App (Backend + Frontend)

Backend (FastAPI):

```bash
poetry install
poetry run uvicorn backend.main:app --reload
```

Frontend (Vue3 + Vuetify via Vite):

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies API calls to `http://localhost:8000` and report JSON files are available at `/reports/<run_dir>/<user>_report.json`.

API response includes:
```
{
	...,
	"run_dir": "20250101T120501Z_ab12cd",
	"report_files": [
		 {"user": "Alice Smith", "filename": "alice_smith_report.json", "relative_path": "20250101T120501Z_ab12cd/alice_smith_report.json"},
		 ...
	]
}
```
Use `relative_path` under `/reports/` to download.
