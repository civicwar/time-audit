import os
import json
import pandas as pd
from io import StringIO
from typing import Optional, Dict, Any


def convert_decimal_to_hm(decimal_hours: float) -> str:
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    return f"{hours}h {minutes}m"


def generate_time_audit(
    csv_content: str,
    big_task_hours: float = 8.0,
    output_dir: Optional[str] = None,
    write_reports: bool = True,
) -> Dict[str, Any]:
    """Generate time audit statistics and (optionally) write per-user JSON reports.

    Parameters
    ----------
    csv_content: Raw CSV string exported from Clockify detailed report (with the same columns expected previously).
    big_task_hours: Threshold above which a task is considered very big.
    output_dir: Directory to write per-user JSON reports. Used only if write_reports is True.
    write_reports: Whether to write JSON report files. If False, function only returns structures.

    Returns
    -------
    A dictionary with keys:
        overlap_per_user
        time_stats (total_time, time_per_user)
        small_tasks_per_user (duration < 0.01)
        big_tasks_per_user (duration > big_task_hours)
        report_by_user_by_date (nested dict user -> date -> list[task dict])
        big_task_hours (echo of threshold)
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

    if write_reports:
        if output_dir is None:
            output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for user, data in report_by_user_by_date.items():
            json_file_path = os.path.join(
                output_dir, f"{user.replace(' ', '_').lower()}_report.json"
            )
            with open(json_file_path, "w") as f:
                json.dump(data, f, indent=4)

    return {
        "overlap_per_user": overlap_per_user,
        "time_stats": time_stats,
        "small_tasks_per_user": small_tasks_per_user,
        "big_tasks_per_user": big_tasks_per_user,
        "report_by_user_by_date": report_by_user_by_date,
        "big_task_hours": big_task_hours,
    }
