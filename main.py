import os
import pandas as pd
import json

# Load the CSV data from the new file
file_path_new = "report.csv"

if not os.path.exists(file_path_new):
    print("The report.csv file is needed.")
    print("You can export it from https://app.clockify.me/reports/detailed")
    exit()

data_new = pd.read_csv(file_path_new)

# Combine the date and time columns into datetime objects
data_new["Start Datetime"] = pd.to_datetime(
    data_new["Start Date"] + " " + data_new["Start Time"], dayfirst=True
)
data_new["End Datetime"] = pd.to_datetime(
    data_new["End Date"] + " " + data_new["End Time"], dayfirst=True
)


# Function to convert decimal duration to hours and minutes
def convert_decimal_to_hm(decimal_hours):
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    return f"{hours}h {minutes}m"


data_grouped = data_new.groupby("User")

overlap_per_user = {}
time_stats = {"total_time": 0, "time_per_user": {}}
small_tasks_per_user = {}

for user, group in data_grouped:
    overlap_per_user[user] = []
    small_tasks_per_user[user] = []
    time_stats["time_per_user"][user] = 0

    group_sorted = group.sort_values("Start Datetime")

    for i in range(len(group_sorted) - 1):
        if (
            group_sorted.iloc[i]["End Datetime"]
            > group_sorted.iloc[i + 1]["Start Datetime"]
        ):
            overlap_per_user[user].append(
                {
                    "task1 start-end": group_sorted.iloc[i]["Start Datetime"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
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
                    "datetime": group_sorted.iloc[i]["Start Datetime"].strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "duration": group_sorted.iloc[i]["Duration (decimal)"],
                }
            )

time_stats["total_time"] = data_new["Duration (decimal)"].sum()
time_stats["time_per_user"] = (
    data_new.groupby("User")
    .agg({"Duration (decimal)": "sum"})
    .to_dict()["Duration (decimal)"]
)

print("Overlap per user")
print(json.dumps(overlap_per_user, indent=4))

print("Time stats")
print(json.dumps(time_stats, indent=4))

print("Very Small tasks per user (duration < 0.01)")
print(json.dumps(small_tasks_per_user, indent=4))


grouping_by_user_by_date = (
    data_new.groupby(["User", "Start Date", "Description"])
    .agg({"Duration (decimal)": "sum"})
    .reset_index()
)

report_by_user_by_date = {}
# Populate the dictionary with the grouped data
for index, row in grouping_by_user_by_date.iterrows():
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


# Create the output directory if it doesn't exist
output_dir = "output"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Save each user's report to a separate JSON file in the output directory
for user, data in report_by_user_by_date.items():
    json_file_path = os.path.join(
        output_dir, f"{user.replace(' ', '_').lower()}_report.json"
    )
    with open(json_file_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Report for {user} has been saved to {json_file_path}")
