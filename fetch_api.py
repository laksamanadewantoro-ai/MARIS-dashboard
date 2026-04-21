import requests
import sqlite3
import time
from datetime import datetime, timezone

DB = "barometer.db"

# =========================
# CREATE DB + TABLE SAFE
# =========================
conn = sqlite3.connect(DB)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pressure_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pressure REAL,
    wind_speed REAL,
    wave_height REAL,
    created_at TEXT,
    location TEXT DEFAULT 'Pulau Pabelokan'
)
""")

conn.commit()

print("MARIS fetch system started...")

# =========================
# MAIN LOOP
# =========================
while True:
    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": -5.5,
            "longitude": 106.5,
            "hourly": "wind_speed_10m,pressure_msl",
            "forecast_days": 1
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print("[ERROR] API status:", response.status_code)
            time.sleep(60)
            continue

        data = response.json()

        if "hourly" not in data:
            print("[ERROR] Invalid API response")
            time.sleep(60)
            continue

        wind = data["hourly"]["wind_speed_10m"][0]
        pressure = data["hourly"]["pressure_msl"][0]

        wave = round(wind * 0.1, 2)

        now = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO pressure_data (pressure, wind_speed, wave_height, created_at, location)
            VALUES (?, ?, ?, ?, ?)
        """, (pressure, wind, wave, now, "Pulau Pabelokan"))

        conn.commit()

        print(f"[OK] wind={wind} wave={wave} pressure={pressure}")

    except Exception as e:
        print("[ERROR]", e)

    time.sleep(60)
