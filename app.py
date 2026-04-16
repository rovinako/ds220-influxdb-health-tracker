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
st.caption("InfluxDB 3 • Simulated Data + Dataset Data")
st.markdown(
    """
    Analyze **health tracking trends** stored in **InfluxDB 3**, using both
    **simulated live data** and a **real fitness tracker dataset**.
    """
)

if not INFLUXDB_TOKEN:
    st.error("Missing INFLUXDB3_AUTH_TOKEN in this terminal session.")
    st.stop()

sql = """
SELECT time, user_id, source, heart_rate, steps, calories_burned, sleep_hours
FROM health_metrics
ORDER BY time
LIMIT 5000
"""

response = requests.get(
    f"{INFLUXDB_URL}/api/v3/query_sql",
    headers={"Authorization": f"Bearer {INFLUXDB_TOKEN}"},
    params={
        "db": DATABASE,
        "q": sql,
        "format": "csv",
    },
    timeout=60,
)

if response.status_code != 200:
    st.error(f"Query failed: {response.text}")
    st.stop()

df = pd.read_csv(StringIO(response.text))

if df.empty:
    st.warning("No data found.")
    st.stop()

df["time"] = pd.to_datetime(df["time"], format="mixed", errors="coerce")
df = df.dropna(subset=["time"])

numeric_cols = ["heart_rate", "steps", "calories_burned", "sleep_hours"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=numeric_cols)
df["user_id"] = df["user_id"].astype(str)

st.sidebar.header("Filters")

source_filter = st.sidebar.selectbox(
    "Data Source",
    ["all", "simulated", "dataset"]
)

users = ["all"] + sorted(df["user_id"].unique().tolist())
selected_user = st.sidebar.selectbox("User", users)

metric_filter = st.sidebar.selectbox(
    "Main Metric",
    ["steps", "heart_rate", "calories_burned", "sleep_hours"]
)

min_date = df["time"].min().date()
max_date = df["time"].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if source_filter != "all":
    df = df[df["source"] == source_filter]

if selected_user != "all":
    df = df[df["user_id"] == selected_user]

if len(date_range) == 2:
    start_date, end_date = date_range
    df = df[
        (df["time"].dt.date >= start_date) &
        (df["time"].dt.date <= end_date)
    ]

if df.empty:
    st.warning("No data matches the current filters.")
    st.stop()

df_viz = df.copy()
df_viz["date"] = df_viz["time"].dt.date

daily_summary = df_viz.groupby(["date", "source"], as_index=False).agg({
    "steps": "sum",
    "heart_rate": "mean",
    "sleep_hours": "mean",
    "calories_burned": "sum"
})

st.markdown("### Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Heart Rate", f"{df['heart_rate'].mean():.1f} bpm")
col2.metric("Total Steps", f"{df['steps'].sum():,.0f}")
col3.metric("Avg Sleep", f"{df['sleep_hours'].mean():.1f} hrs")
col4.metric("Avg Calories", f"{df['calories_burned'].mean():,.1f}")

latest = df.sort_values("time").iloc[-1]

st.markdown("### Latest Activity")

colA, colB, colC, colD = st.columns(4)
colA.metric("User", latest["user_id"])
colB.metric("Steps", f"{latest['steps']:.0f}")
colC.metric("Heart Rate", f"{latest['heart_rate']:.0f}")
colD.metric("Sleep Hours", f"{latest['sleep_hours']:.1f}")

st.subheader(f"Daily {metric_filter.replace('_', ' ').title()} Trend")

fig_main = px.line(
    daily_summary,
    x="date",
    y=metric_filter,
    color="source",
    markers=True,
    template="simple_white"
)

fig_main.update_layout(
    height=420,
    xaxis_title="Date",
    yaxis_title=metric_filter.replace("_", " ").title(),
    legend_title="Source",
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig_main, use_container_width=True)

st.subheader("Daily Steps")

daily_steps = daily_summary.groupby("date", as_index=False)["steps"].sum()

fig_steps = px.bar(
    daily_steps,
    x="date",
    y="steps",
    template="simple_white"
)

fig_steps.update_layout(
    height=380,
    xaxis_title="Date",
    yaxis_title="Total Steps",
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig_steps, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Average Daily Heart Rate")
    hr_daily = daily_summary.groupby("date", as_index=False)["heart_rate"].mean()
    fig_hr = px.line(
        hr_daily,
        x="date",
        y="heart_rate",
        markers=True,
        template="simple_white"
    )
    fig_hr.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_hr, use_container_width=True)

with right:
    st.subheader("Average Daily Sleep")
    sleep_daily = daily_summary.groupby("date", as_index=False)["sleep_hours"].mean()
    fig_sleep = px.line(
        sleep_daily,
        x="date",
        y="sleep_hours",
        markers=True,
        template="simple_white"
    )
    fig_sleep.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_sleep, use_container_width=True)

st.subheader("Source Comparison")

source_summary = df.groupby("source", as_index=False).agg({
    "heart_rate": "mean",
    "steps": "sum",
    "sleep_hours": "mean",
    "calories_burned": "mean"
})

compare_metric = st.selectbox(
    "Compare by Metric",
    ["heart_rate", "steps", "sleep_hours", "calories_burned"]
)

fig_compare = px.bar(
    source_summary,
    x="source",
    y=compare_metric,
    color="source",
    text_auto=".2s",
    template="simple_white"
)

fig_compare.update_layout(
    height=350,
    showlegend=False,
    xaxis_title="Source",
    yaxis_title=compare_metric.replace("_", " ").title(),
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig_compare, use_container_width=True)

st.subheader("Top 10 Active Users")

top_users = (
    df.groupby("user_id", as_index=False)["steps"]
    .sum()
    .sort_values("steps", ascending=False)
    .head(10)
)

fig_users = px.bar(
    top_users,
    x="steps",
    y="user_id",
    orientation="h",
    template="simple_white"
)

fig_users.update_layout(
    height=400,
    xaxis_title="Total Steps",
    yaxis_title="User ID",
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig_users, use_container_width=True)

st.subheader("Health Insights")
insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.write(f"Highest heart rate: {df['heart_rate'].max():.1f}")
    st.write(f"Lowest sleep hours: {df['sleep_hours'].min():.1f}")
    st.write(f"Latest timestamp: {df['time'].max()}")

with insight_col2:
    st.write(f"Total records: {len(df):,}")
    st.write(f"Total steps: {df['steps'].sum():,.0f}")
    st.write(f"Average calories burned: {df['calories_burned'].mean():.1f}")

st.subheader("High Heart Rate Alerts")
alerts = df[df["heart_rate"] > 100][["time", "user_id", "source", "heart_rate"]]
alerts = alerts.sort_values("heart_rate", ascending=False).head(10)

if alerts.empty:
    st.success("No high heart rate alerts found.")
else:
    st.dataframe(alerts, use_container_width=True)

with st.expander("Show Raw Data"):
    st.dataframe(
        df.sort_values("time", ascending=False),
        use_container_width=True
    )