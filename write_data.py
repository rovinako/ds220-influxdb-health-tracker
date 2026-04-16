import os
import random
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

INFLUXDB_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8181")
DATABASE = os.getenv("INFLUXDB_DATABASE", "health_data")

if not INFLUXDB_TOKEN:
    raise ValueError("Missing INFLUXDB3_AUTH_TOKEN. Check your .env file.")

url = f"{INFLUXDB_URL}/api/v3/write_lp"

headers = {
    "Authorization": f"Bearer {INFLUXDB_TOKEN}",
    "Content-Type": "text/plain; charset=utf-8",
}

start = datetime.now(timezone.utc) - timedelta(days=7)
lines = []

for i in range(7 * 24):
    t = start + timedelta(hours=i)
    timestamp = int(t.timestamp() * 1e9)

    heart_rate = random.randint(60, 100)
    steps = random.randint(100, 1200)
    calories = random.randint(50, 200)
    sleep = round(random.uniform(5, 9), 1)

    line = (
    f"health_metrics,user_id=student1,source=simulated "
    f"heart_rate={heart_rate},steps={steps},"
    f"calories_burned={calories},sleep_hours={sleep} {timestamp}"
)
    lines.append(line)

data = "\n".join(lines)

response = requests.post(
    f"{url}?db={DATABASE}",
    headers=headers,
    data=data,
    timeout=30,
)

print("Status:", response.status_code)
print("Response:", response.text or "[no body]")
response.raise_for_status()
print(f"Successfully wrote {len(lines)} records.")