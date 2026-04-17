import os
from io import StringIO

import pandas as pd
import requests
import streamlit as st
import plotly.express as px

INFLUXDB_TOKEN = os.getenv("INFLUXDB3_AUTH_TOKEN")
INFLUXDB_URL = "http://localhost:8181"
DATABASE = "health_data"

st.set_page_config(
    page_title="Health Tracking Dashboard",
    page_icon="❤️",
    layout="wide"
)

st.title("Health Tracking Dashboard")
st.caption("InfluxDB 3 • Personal Health View")
st.markdown(
    """
    This dashboard shows **health trends for a single user**, using data stored in **InfluxDB 3**.
    Data includes both **real dataset records** and **simulated live data**.
    """
)

if not INFLUXDB_TOKEN:
    st.error("Missing INFLUXDB3_AUTH_TOKEN.")
    st.stop()

# Query data
sql = """
SELECT time, user_id, source, heart_rate, steps, calories_burned, sleep_hours
FROM health_metrics
ORDER BY time
LIMIT 5000
"""

response = requests.get(
    f"{INFLUXDB_URL}/api/v3/query_sql",
    headers={"Authorization": f"Bearer {INFLUXDB_TOKEN}"},
    params={"db": DATABASE, "q": sql, "format": "csv"},
    timeout=60,
)

if response.status_code != 200:
    st.error(f"Query failed: {response.text}")
    st.stop()

df = pd.read_csv(StringIO(response.text))

if df.empty:
    st.warning("No data found.")
    st.stop()

# Clean data
df["time"] = pd.to_datetime(df["time"], format="mixed", errors="coerce")
df = df.dropna(subset=["time"])

for col in ["heart_rate", "steps", "calories_burned", "sleep_hours"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna()
df["user_id"] = df["user_id"].astype(str)

# Sidebar
st.sidebar.header("Dashboard Filters")

# SINGLE USER (no "all")
users = sorted(df["user_id"].unique().tolist())

selected_user = st.sidebar.selectbox(
    "Select User",
    users,
    index=0
)

source_filter = st.sidebar.selectbox(
    "Data Source",
    ["all", "simulated", "dataset"]
)

metric_filter = st.sidebar.selectbox(
    "Main Metric",
    ["steps", "heart_rate", "calories_burned", "sleep_hours"]
)

# Filter data
df = df[df["user_id"] == selected_user]

if source_filter != "all":
    df = df[df["source"] == source_filter]

# Date filter
min_date = df["time"].min().date()
max_date = df["time"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date)
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[
        (df["time"].dt.date >= start_date) &
        (df["time"].dt.date <= end_date)
    ]

if df.empty:
    st.warning("No data matches filters.")
    st.stop()

# Prepare daily data
df["date"] = df["time"].dt.date

daily = df.groupby("date", as_index=False).agg({
    "steps": "sum",
    "heart_rate": "mean",
    "sleep_hours": "mean",
    "calories_burned": "sum"
})

# KPI
st.markdown("### Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Avg Heart Rate", f"{df['heart_rate'].mean():.1f} bpm")
c2.metric("Total Steps", f"{df['steps'].sum():,.0f}")
c3.metric("Avg Sleep", f"{df['sleep_hours'].mean():.1f} hrs")
c4.metric("Avg Calories", f"{df['calories_burned'].mean():,.1f}")

# Latest
latest = df.sort_values("time").iloc[-1]

st.markdown("### Latest Activity")

l1, l2, l3, l4 = st.columns(4)
l1.metric("User", f"User {latest['user_id']}")
l2.metric("Steps", f"{latest['steps']:,.0f}")
l3.metric("Heart Rate", f"{latest['heart_rate']:.0f}")
l4.metric("Sleep", f"{latest['sleep_hours']:.1f} hrs")

# Main chart
st.subheader("Daily Trend")

fig_main = px.line(
    daily,
    x="date",
    y=metric_filter,
    markers=True,
    template="simple_white"
)

fig_main.update_layout(
    height=420,
    margin=dict(l=10, r=10, t=30, b=10)
)

st.plotly_chart(fig_main, use_container_width=True)

# Steps chart
st.subheader("Daily Steps")

fig_steps = px.bar(
    daily,
    x="date",
    y="steps",
    template="simple_white"
)

fig_steps.update_layout(
    height=380,
    margin=dict(l=10, r=10, t=30, b=10)
)

st.plotly_chart(fig_steps, use_container_width=True)

# Two charts
left, right = st.columns(2)

with left:
    st.subheader("Heart Rate")
    fig_hr = px.line(
        daily,
        x="date",
        y="heart_rate",
        markers=True,
        template="simple_white"
    )
    fig_hr.update_layout(height=350)
    st.plotly_chart(fig_hr, use_container_width=True)

with right:
    st.subheader("Sleep")
    fig_sleep = px.line(
        daily,
        x="date",
        y="sleep_hours",
        markers=True,
        template="simple_white"
    )
    fig_sleep.update_layout(height=350)
    st.plotly_chart(fig_sleep, use_container_width=True)

# Insights
st.subheader("Insights")

i1, i2 = st.columns(2)

with i1:
    st.write(f"Highest heart rate: {df['heart_rate'].max():.1f}")
    st.write(f"Lowest sleep: {df['sleep_hours'].min():.1f}")

with i2:
    st.write(f"Total records: {len(df):,}")
    st.write(f"Total steps: {df['steps'].sum():,.0f}")

# Alerts
st.subheader("High Heart Rate Alerts")

alerts = df[df["heart_rate"] > 100].sort_values("heart_rate", ascending=False).head(10)

if alerts.empty:
    st.success("No alerts.")
else:
    st.dataframe(alerts[["time", "heart_rate"]])

# Raw data
with st.expander("Show Raw Data"):
    st.dataframe(df.sort_values("time", ascending=False))