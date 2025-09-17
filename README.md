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

If `output_dir` is provided (or left as default) and `write_reports=True`, per-user JSON files are written (one file each) containing daily grouped tasks.

### CLI Wrapper

Running the repository directly (or `python main.py`) expects a `report.csv` in the working directory and will output summaries and JSON reports in `./output`.

```bash
python main.py
```

### Future Web Integration

The refactored function signature is:

```python
generate_time_audit(csv_content: str, big_task_hours: float = 8.0, output_dir: str | None = None, write_reports: bool = True) -> dict
```

This allows easy integration into a web endpoint that accepts an uploaded CSV and returns JSON.
