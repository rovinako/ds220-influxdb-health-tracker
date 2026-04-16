import os
from io import StringIO

import requests
import pandas as pd
import matplotlib.pyplot as plt

INFLUXDB_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUXDB_URL = "http://localhost:8181"
DATABASE = "health_data"

if not INFLUXDB_TOKEN:
    raise ValueError("Missing INFLUXDB3_AUTH_TOKEN in this terminal session.")

sql = """
SELECT time, steps
FROM health_metrics
ORDER BY time
LIMIT 200
"""

response = requests.get(
    f"{INFLUXDB_URL}/api/v3/query_sql",
    headers={
        "Authorization": f"Bearer {INFLUXDB_TOKEN}",
    },
    params={
        "db": DATABASE,
        "q": sql,
        "format": "csv",
    },
    timeout=30,
)

print("Status:", response.status_code)
print("Raw response preview:")
print(response.text[:500])

response.raise_for_status()

df = pd.read_csv(StringIO(response.text))

if df.empty:
    raise SystemExit("No data returned from query.")

df["time"] = pd.to_datetime(df["time"])
df["steps"] = pd.to_numeric(df["steps"])

plt.figure(figsize=(10, 5))
plt.plot(df["time"], df["steps"])
plt.xlabel("Time")
plt.ylabel("Steps")
plt.title("Steps Over Time")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("steps_over_time.png")
print("Chart saved as steps_over_time.png")