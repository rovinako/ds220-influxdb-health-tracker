import os
import pandas as pd
import requests

INFLUXDB_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUXDB_URL = "http://localhost:8181"
DATABASE = "health_data"

if not INFLUXDB_TOKEN:
    raise ValueError("Missing INFLUXDB3_AUTH_TOKEN")

df = pd.read_csv("data/health_dataset.csv").head(20000)

# Convert date column
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date"])

lines = []

for index, row in df.iterrows():
    try:
        timestamp_ns = int(row["date"].timestamp() * 1e9)

        user_id = str(row["user_id"])
        heart_rate = float(row["heart_rate_avg"])
        steps = float(row["steps"])
        calories = float(row["calories_burned"])
        sleep = float(row["sleep_hours"])

        line = (
            f"health_metrics,user_id={user_id},source=dataset "
            f"heart_rate={heart_rate},steps={steps},"
            f"calories_burned={calories},sleep_hours={sleep} {timestamp_ns}"
        )
        lines.append(line)

    except Exception as e:
        print(f"Skipping row {index}: {e}")

BATCH_SIZE = 5000
total_sent = 0

for start in range(0, len(lines), BATCH_SIZE):
    batch = lines[start:start + BATCH_SIZE]
    payload = "\n".join(batch)

    response = requests.post(
        f"{INFLUXDB_URL}/api/v3/write_lp?db={DATABASE}",
        headers={
            "Authorization": f"Bearer {INFLUXDB_TOKEN}",
            "Content-Type": "text/plain; charset=utf-8",
        },
        data=payload,
        timeout=60,
    )

    if response.status_code not in (200, 204):
        print(f"Batch failed at rows {start} to {start + len(batch)}")
        print("Status:", response.status_code)
        print("Response:", response.text or "[no body]")
        break

    total_sent += len(batch)
    print(f"Imported {total_sent} / {len(lines)} rows")

print(f"Finished. Successfully imported {total_sent} rows.")