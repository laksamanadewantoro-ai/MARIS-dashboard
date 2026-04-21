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
        ["All", "Pulau Pabelokan", "Kali Japat - Jakarta Utara"]
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

    # check table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pressure_data'
    """)

    if cursor.fetchone() is None:
        st.error("Table 'pressure_data' not found in database")
        st.stop()

    df = pd.read_sql_query(
        "SELECT * FROM pressure_data ORDER BY created_at DESC LIMIT 500",
        conn
    )

    conn.close()

except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

# =========================
# EMPTY DATA CHECK
# =========================
if df.empty:
    st.warning("No data available. Run fetch_api.py")
    st.stop()

# =========================
# CLEAN DATA
# =========================
df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
df = df.dropna(subset=["created_at"]).sort_values("created_at")

if df.empty:
    st.warning("Invalid timestamp data in database")
    st.stop()

# =========================
# DEFAULT LOCATION
# =========================
if "location" not in df.columns:
    df["location"] = "Pulau Pabelokan"

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

wind = float(latest.get("wind_speed", 0))
wave = float(latest.get("wave_height", 0))
pressure = float(latest.get("pressure", 0))
created_at = latest["created_at"]

# =========================
# STATUS ENGINE
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
# KPI SECTION
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
<div class="kpi-value" style="color:{color};">{status}</div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# MAP
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Location Monitoring</div>', unsafe_allow_html=True)

coords = {
    "Pulau Pabelokan": (-5.5, 106.5),
    "Kali Japat - Jakarta Utara": (-6.10, 106.88)
}

df_map = df.groupby("location").tail(1).copy()

df_map["lat"] = df_map["location"].apply(lambda x: coords.get(x, (-5.5, 106.5))[0])
df_map["lon"] = df_map["location"].apply(lambda x: coords.get(x, (-5.5, 106.5))[1])

def get_status(row):
    if row["wave_height"] > 2 or row["wind_speed"] > 20:
        return "DANGER"
    elif row["wave_height"] > 1 or row["wind_speed"] > 12:
        return "WARNING"
    return "SAFE"

df_map["status"] = df_map.apply(get_status, axis=1)

fig_map = px.scatter_mapbox(
    df_map,
    lat="lat",
    lon="lon",
    color="status",
    hover_name="location",
    hover_data=["wind_speed", "wave_height", "pressure", "created_at"],
    zoom=5,
    height=420
)

fig_map.update_layout(
    mapbox_style="open-street-map",
    margin=dict(l=0, r=0, t=0, b=0)
)

st.plotly_chart(fig_map, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# CHARTS
# =========================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-title">Environmental Trends</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df["created_at"], y=df["wind_speed"], mode="lines"))
fig1.update_layout(template="plotly_dark", height=280, title="Wind Speed")
col1.plotly_chart(fig1, use_container_width=True)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df["created_at"], y=df["wave_height"], mode="lines"))
fig2.update_layout(template="plotly_dark", height=280, title="Wave Height")
col2.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=df["created_at"], y=df["pressure"], mode="lines"))
fig3.update_layout(template="plotly_dark", height=280, title="Pressure")
col3.plotly_chart(fig3, use_container_width=True)

fig4 = go.Figure(go.Indicator(
    mode="gauge+number",
    value=wind,
    title={'text': "Wind Speed"},
    gauge={
        'axis': {'range': [0, 40]},
        'steps': [
            {'range': [0, 12], 'color': "#1e293b"},
            {'range': [12, 20], 'color': "#f59e0b"},
            {'range': [20, 40], 'color': "#ef4444"}
        ]
    }
))

fig4.update_layout(template="plotly_dark", height=280)
col4.plotly_chart(fig4, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.caption(f"Last Update: {created_at}")
