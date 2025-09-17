import os
import json
from time_audit import generate_time_audit


def main():
    file_path = "report.csv"
    big_task_duration = 8.0

    if not os.path.exists(file_path):
        print("The report.csv file is needed.")
        print("You can export it from https://app.clockify.me/reports/detailed")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        csv_content = f.read()

    results = generate_time_audit(
        csv_content=csv_content, big_task_hours=big_task_duration, output_dir="output"
    )

    print("Overlap per user")
    print(json.dumps(results["overlap_per_user"], indent=4))

    print("Time stats")
    print(json.dumps(results["time_stats"], indent=4))

    print("Very Small tasks per user (duration < 0.01)")
    print(json.dumps(results["small_tasks_per_user"], indent=4))

    print(
        f"Very big tasks per user (duration > {results['big_task_hours']} hours)"
    )
    print(json.dumps(results["big_tasks_per_user"], indent=4))

    print("Per-user reports written to output directory.")


if __name__ == "__main__":
    main()
