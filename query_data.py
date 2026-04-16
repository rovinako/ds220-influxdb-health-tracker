import os
import requests
import pandas as pd
from io import StringIO

INFLUXDB_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUXDB_URL = "http://localhost:8181"
DATABASE = "health_data"

headers = {
    "Authorization": f"Bearer {INFLUXDB_TOKEN}",
}

queries = {
    "Average Heart Rate": "SELECT AVG(heart_rate) AS avg_heart_rate FROM health_metrics",
    "Total Steps": "SELECT SUM(steps) AS total_steps FROM health_metrics",
    "Average Sleep Hours": "SELECT AVG(sleep_hours) AS avg_sleep_hours FROM health_metrics",
    "Average Calories Burned": "SELECT AVG(calories_burned) AS avg_calories_burned FROM health_metrics",
}

for title, sql in queries.items():
    response = requests.get(
        f"{INFLUXDB_URL}/api/v3/query_sql",
        headers=headers,
        params={
            "db": DATABASE,
            "q": sql,
            "format": "csv",
        },
        timeout=30,
    )

    print("\n" + "=" * 40)
    print(title)
    print("=" * 40)

    if response.status_code != 200:
        print("Error:", response.text)
        continue

    df = pd.read_csv(StringIO(response.text))
    print(df.to_string(index=False))