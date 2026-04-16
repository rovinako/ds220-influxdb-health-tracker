import os
from io import StringIO

import requests
import pandas as pd
import matplotlib.pyplot as plt

INFLUXDB_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUXDB_URL = "http://localhost:8181"
DATABASE = "health_data"

response = requests.get(
    f"{INFLUXDB_URL}/api/v3/query_sql",
    headers={
        "Authorization": f"Bearer {INFLUXDB_TOKEN}",
    },
    params={
        "db": DATABASE,
        "q": "SELECT time, heart_rate FROM health_metrics ORDER BY time LIMIT 200",
        "format": "csv",
    },
    timeout=30,
)

response.raise_for_status()

df = pd.read_csv(StringIO(response.text))
df["time"] = pd.to_datetime(df["time"])
df["heart_rate"] = pd.to_numeric(df["heart_rate"])

plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["heart_rate"])
plt.xlabel("Time")
plt.ylabel("Heart Rate")
plt.title("Heart Rate Over Time")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("heart_rate_over_time.png")
print("Chart saved as heart_rate_over_time.png")