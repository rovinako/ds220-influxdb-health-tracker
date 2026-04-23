# Health Tracking Dashboard (InfluxDB)

## Overview
This project is a health tracking dashboard built using **InfluxDB 3**, a NoSQL time-series database.

It stores and analyzes health data such as:
- steps
- heart rate
- sleep hours
- calories burned

The system combines:
- simulated real-time data
- a real fitness dataset

and displays everything in an interactive dashboard.

---

## Features
- Stores time-series health data in InfluxDB
- Imports data from a real dataset
- Generates simulated health data
- Queries data using HTTP API
- Interactive dashboard built with Streamlit
- Filters by:
  - data source (simulated vs dataset)
  - user
  - date range
- Visual charts for trends and comparisons

---

## Technologies Used
- InfluxDB 3 (NoSQL database)
- Python
- Pandas
- Streamlit
- Plotly

---

## How to Run

### 1. Start InfluxDB
```bash
influxdb3 serve --node-id default --object-store file --data-dir /opt/homebrew/var/lib/influxdb

/opt/homebrew/opt/influxdb/bin/influxdb3 serve --node-id local --object-store file --data-dir ~/.influxdb3