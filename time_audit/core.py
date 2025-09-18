import os
import json
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
from io import StringIO
from typing import Optional, Dict, Any, List
import uuid


def convert_decimal_to_hm(decimal_hours: float) -> str:
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    return f"{hours}h {minutes}m"


def generate_time_audit(
    csv_content: str,
    big_task_hours: float = 8.0,
    output_dir: Optional[str] = None,
    write_reports: bool = True,
    clean_output_dir: bool = False,  # deprecated: retained for compatibility, ignored in favor of per-request subdirs
    retention_hours: int = 24,
) -> Dict[str, Any]:
    """Generate time audit statistics and (optionally) write per-user JSON reports.

    Parameters
    ----------
    csv_content: Raw CSV string exported from Clockify detailed report (with the same columns expected previously).
    big_task_hours: Threshold above which a task is considered very big.
    output_dir: Directory to write per-user JSON reports. Used only if write_reports is True.
    write_reports: Whether to write JSON report files. If False, function only returns structures.
    clean_output_dir: (Deprecated) Ignored; previous behavior replaced with per-request subdirectories for isolation.
    retention_hours: Number of hours to retain past run directories. Directories older than this will be deleted.

    Returns
    -------
    A dictionary with keys:
        overlap_per_user
        time_stats (total_time, time_per_user)
        small_tasks_per_user (duration < 0.01)
        big_tasks_per_user (duration > big_task_hours)
        report_by_user_by_date (nested dict user -> date -> list[task dict])
    big_task_hours (echo of threshold)
    report_files (list of {user, filename, relative_path}) if write_reports is True else empty list
    run_dir (name of the per-request subdirectory) when write_reports True else None
    """
    # Read CSV from string
    data_new = pd.read_csv(StringIO(csv_content))

    # Combine the date and time columns into datetime objects
    data_new["Start Datetime"] = pd.to_datetime(
        data_new["Start Date"] + " " + data_new["Start Time"], dayfirst=True
    )
    data_new["End Datetime"] = pd.to_datetime(
        data_new["End Date"] + " " + data_new["End Time"], dayfirst=True
    )

    data_grouped = data_new.groupby("User")

    overlap_per_user = {}
    time_stats = {"total_time": 0, "time_per_user": {}}
    small_tasks_per_user = {}
    big_tasks_per_user = {}

    for user, group in data_grouped:
        overlap_per_user[user] = []
        small_tasks_per_user[user] = []
        big_tasks_per_user[user] = []
        time_stats["time_per_user"][user] = 0

        group_sorted = group.sort_values("Start Datetime")

        for i in range(len(group_sorted) - 1):
            if (
                group_sorted.iloc[i]["End Datetime"]
                > group_sorted.iloc[i + 1]["Start Datetime"]
            ):
                overlap_per_user[user].append(
                    {
                        "task1 start-end": group_sorted.iloc[i][
                            "Start Datetime"
                        ].strftime("%Y-%m-%d %H:%M:%S")
                        + " - "
                        + group_sorted.iloc[i]["End Datetime"].strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "task2 start-end": group_sorted.iloc[i + 1][
                            "Start Datetime"
                        ].strftime("%Y-%m-%d %H:%M:%S")
                        + " - "
                        + group_sorted.iloc[i + 1]["End Datetime"].strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "task1": group_sorted.iloc[i]["Description"],
                        "task2": group_sorted.iloc[i + 1]["Description"],
                    }
                )

            if group_sorted.iloc[i]["Duration (decimal)"] < 0.01:
                small_tasks_per_user[user].append(
                    {
                        "task": group_sorted.iloc[i]["Description"],
                        "datetime": group_sorted.iloc[i][
                            "Start Datetime"
                        ].strftime("%Y-%m-%d %H:%M:%S"),
                        "duration": group_sorted.iloc[i]["Duration (decimal)"],
                    }
                )
            if group_sorted.iloc[i]["Duration (decimal)"] > big_task_hours:
                big_tasks_per_user[user].append(
                    {
                        "task": group_sorted.iloc[i]["Description"],
                        "datetime": group_sorted.iloc[i][
                            "Start Datetime"
                        ].strftime("%Y-%m-%d %H:%M:%S"),
                        "duration": group_sorted.iloc[i]["Duration (decimal)"],
                    }
                )

    time_stats["total_time"] = data_new["Duration (decimal)"].sum()
    time_stats["time_per_user"] = (
        data_new.groupby("User")
        .agg({"Duration (decimal)": "sum"})
        .to_dict()["Duration (decimal)"]
    )

    grouping_by_user_by_date = (
        data_new.groupby(["User", "Start Date", "Description"])
        .agg({"Duration (decimal)": "sum"})
        .reset_index()
    )

    report_by_user_by_date = {}
    for _, row in grouping_by_user_by_date.iterrows():
        user = row["User"]
        date = row["Start Date"]
        description = row["Description"]
        duration_decimal = row["Duration (decimal)"]
        duration_hm = convert_decimal_to_hm(duration_decimal)

        if user not in report_by_user_by_date:
            report_by_user_by_date[user] = {}
        if date not in report_by_user_by_date[user]:
            report_by_user_by_date[user][date] = []

        report_by_user_by_date[user][date].append(
            {
                "description": description,
                "duration": duration_decimal,
                "duration_hm": duration_hm,
            }
        )

    report_files: List[Dict[str, str]] = []
    run_dir_name: Optional[str] = None
    if write_reports:
        if output_dir is None:
            output_dir = "output"
        # Ensure base directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Retention: delete run directories older than retention_hours
        now = datetime.now(timezone.utc)
        for entry in os.scandir(output_dir):
            if entry.is_dir():
                name = entry.name
                ts_part = name.split("_")[0]
                try:
                    ts_dt = datetime.strptime(ts_part, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                if now - ts_dt > timedelta(hours=retention_hours):
                    try:
                        shutil.rmtree(entry.path)
                    except OSError:
                        pass

        # Create per-request subdirectory
        ts = now.strftime("%Y%m%dT%H%M%SZ")
        run_dir_name = f"{ts}_{uuid.uuid4().hex[:6]}"
        run_dir_path = os.path.join(output_dir, run_dir_name)
        os.makedirs(run_dir_path, exist_ok=True)

        for user, data in report_by_user_by_date.items():
            safe_user = user.replace(" ", "_").lower()
            filename = f"{safe_user}_report.json"
            json_file_path = os.path.join(run_dir_path, filename)
            with open(json_file_path, "w") as f:
                json.dump(data, f, indent=4)
            report_files.append({
                "user": user,
                "filename": filename,
                "relative_path": f"{run_dir_name}/{filename}",
            })

    return {
        "overlap_per_user": overlap_per_user,
        "time_stats": time_stats,
        "small_tasks_per_user": small_tasks_per_user,
        "big_tasks_per_user": big_tasks_per_user,
        "report_by_user_by_date": report_by_user_by_date,
        "big_task_hours": big_task_hours,
        "report_files": report_files,
        "run_dir": run_dir_name,
    }
