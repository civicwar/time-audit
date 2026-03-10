## Time Audit

Python utilities to analyze Clockify detailed reports.

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

This allows easy integration into a web endpoint that accepts Clockify report data and returns JSON.

### Web App (Backend + Frontend)

Backend (FastAPI):

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn backend.main:app --reload
```

The backend now initializes a local SQLite database automatically at `time_audit.db`.
Create a local `.env` file first and set the admin seed password and Clockify API key there:

```bash
TIME_AUDIT_ADMIN_PASSWORD=change-this-admin-password
TIME_AUDIT_CLOCKIFY_API_KEY=your-clockify-api-key
```

Set `TIME_AUDIT_DATABASE_URL` if you want to point it somewhere else, for example:

```bash
export TIME_AUDIT_DATABASE_URL=sqlite:///./time_audit.db
poetry run alembic upgrade head
poetry run uvicorn backend.main:app --reload
```

Alembic is configured for database migrations. Common commands:

```bash
poetry run alembic revision -m "create example table"
poetry run alembic upgrade head
```

Authentication is now enabled.
Only the `admin` user is created during seeding, and its password is read from `.env` via `TIME_AUDIT_ADMIN_PASSWORD`.

Clockify detailed reports are fetched directly from the Clockify API using `TIME_AUDIT_CLOCKIFY_API_KEY`.
Optional overrides:
- `TIME_AUDIT_CLOCKIFY_WORKSPACE_ID` to pin a specific workspace instead of auto-detecting the active one
- `TIME_AUDIT_CLOCKIFY_API_BASE_URL` to override the standard API host
- `TIME_AUDIT_CLOCKIFY_REPORTS_BASE_URL` to override the reports API host

Login is protected against brute-force attempts with in-memory lockouts by client IP and username.
Tunable environment variables:
- `TIME_AUDIT_LOGIN_MAX_ATTEMPTS_PER_IP` default `10`
- `TIME_AUDIT_LOGIN_MAX_ATTEMPTS_PER_USERNAME` default `5`
- `TIME_AUDIT_LOGIN_ATTEMPT_WINDOW_SECONDS` default `900`
- `TIME_AUDIT_LOGIN_LOCKOUT_SECONDS` default `900`

Private backend endpoints live under `/api/in/...` and frontend private views live under `/in/...`.

Frontend (Vue3 + Vuetify via Vite):

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies API calls to `http://localhost:8000` and report JSON files are available at `/reports/<run_dir>/<user>_report.json`.

In the private workspace, users now select:
- start date
- end date
- timezone

The backend fetches the corresponding Clockify detailed report and runs the existing audit pipeline without requiring CSV upload.

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

Current app status:
- SQLite connection/session management is available in `backend.database`.
- Alembic migration scaffolding is available under `alembic/`.
- Authentication and user management are backed by the `users` table.
- User roles are hardcoded to `Admin`, `Developer`, and `Reviewer`.
- Clockify integration lives in the dedicated `backend.clockify` module.
