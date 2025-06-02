```
# INSTALL PROJECT
docker build -f .devcontainer/Dockerfile -t time-audit .

# RUN A CONTAINER
docker run --volume app:/home/vscode --rm -it time-audit:latest

# IN ANOTHER TERMINAL
docker ps # GRAB THE CONTAINER NAME
docker cp /home/bart/Downloads/Clockify_Time_Report_Detailed_01_05_2025-31_05_2025.csv [CONTAINER_NAME]:/home/vscode

# BACK TO DOCKER CONTAINER
mv Clockify_Time_Report_Detailed_01_05_2025-31_05_2025.csv report.csv
poetry install --no-root
poetry run python main.py
```
