import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="MARIS Dashboard")
st_autorefresh(interval=5000, key="refresh")

# =========================
# STYLE
# =========================
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.block-container { padding: 2rem; }

.card {
    background: linear-gradient(145deg, #0f172a, #1e293b);
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 18px;
}

.kpi {
    background: linear-gradient(145deg, #0f172a, #1e293b);
    padding: 14px;
    border-radius: 12px;
}

.kpi-title {
    color: #94a3b8;
    font-size: 12px;
}

.kpi-value {
    font-size: 22px;
    font-weight: bold;
    color: white;
}

.section-title {
    font-size: 18px;
    color: white;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.image("logo.png", width=140)
    st.markdown("### MARIS")
    st.caption("Marine & Atmospheric Monitoring System")
    st.markdown("---")

    location_filter = st.selectbox(
        "Select Location",
        ["All", "Pulau Pabelokan"]
    )

    st.markdown("---")
    st.success("System Online")

# =========================
# HEADER
# =========================
col1, col2 = st.columns([1, 8])

with col1:
    st.image("logo.png", width=70)

with col2:
    st.markdown("""
    <div style="padding-top:8px;">
        <div style="font-size:26px; font-weight:bold; color:white;">
            MARIS Dashboard
        </div>
        <div style="color:#94a3b8;">
            Marine & Atmospheric Monitoring System | Offshore Monitoring Platform
        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# DATABASE SAFE LOAD
# =========================
DB_PATH = "barometer.db"

if not os.path.exists(DB_PATH):
    st.error("Database file not found. Run fetch_api.py first.")
    st.stop()

try:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pressure_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pressure REAL,
            wind_speed REAL,
            wave_height REAL,
            created_at TEXT,
            location TEXT
        )
    """)
    conn.commit()

    df = pd.read_sql_query(
        "SELECT * FROM pressure_data ORDER BY created_at DESC LIMIT 500",
        conn
    )

    conn.close()

except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

# =========================
# EMPTY CHECK
# =========================
if df.empty:
    st.warning("No data available yet. Please run fetch_api.py first.")
    st.stop()

# =========================
# CLEAN DATA
# =========================
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df = df.dropna(subset=["created_at"]).sort_values("created_at")

if df.empty:
    st.warning("Invalid data in database")
    st.stop()

# =========================
# FILTER
# =========================
if location_filter != "All":
    df = df[df["location"] == location_filter]

if df.empty:
    st.warning("No data for selected location")
    st.stop()

# =========================
# LATEST DATA
# =========================
latest = df.iloc[-1]

wind = float(latest["wind_speed"])
wave = float(latest["wave_height"])
pressure = float(latest["pressure"])
created_at = latest["created_at"]

# =========================
# STATUS
# =========================
status = "SAFE"
color = "#22c55e"

if wave > 2 or wind > 20:
    status = "DANGER"
    color = "#ef4444"
elif wave > 1 or wind > 12:
    status = "WARNING"
    color = "#f59e0b"

# =========================
# ALERT
# =========================
if status == "DANGER":
    st.error("⚠ HIGH SEA STATE DETECTED")
elif status == "WARNING":
    st.warning("⚠ Moderate Sea Condition")
else:
    st.success("✓ Safe Operational Condition")

# =========================
# KPI
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"""
<div class="kpi">
<div class="kpi-title">Wind Speed</div>
<div class="kpi-value">{wind:.2f} kt</div>
</div>
""", unsafe_allow_html=True)

c2.markdown(f"""
<div class="kpi">
<div class="kpi-title">Wave Height</div>
<div class="kpi-value">{wave:.2f} m</div>
</div>
""", unsafe_allow_html=True)

c3.markdown(f"""
<div class="kpi">
<div class="kpi-title">Pressure</div>
<div class="kpi-value">{pressure:.2f} hPa</div>
</div>
""", unsafe_allow_html=True)

c4.markdown(f"""
<div class="kpi">
<div class="kpi-title">Status</div>
<div class="kpi-value" style="color:{color}">{status}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# CHART
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Environmental Trends</div>', unsafe_allow_html=True)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["created_at"], y=df["wind_speed"], mode="lines", name="Wind"))
fig.add_trace(go.Scatter(x=df["created_at"], y=df["wave_height"], mode="lines", name="Wave"))
fig.add_trace(go.Scatter(x=df["created_at"], y=df["pressure"], mode="lines", name="Pressure"))

fig.update_layout(template="plotly_dark", height=400)

st.plotly_chart(fig, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.caption(f"Last Update: {created_at}")
