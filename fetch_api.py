import requests
import sqlite3
import time
import datetime

# ===== LOKASI =====
LOCATIONS = [
    {"name": "Pulau Pabelokan", "lat": -5.5, "lon": 106.5},
    {"name": "Kali Japat - Jakarta Utara", "lat": -6.10, "lon": 106.88}
]

# ===== DB =====
conn = sqlite3.connect("barometer.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS pressure_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location TEXT,
    pressure REAL,
    wind_speed REAL,
    wave_height REAL,
    created_at TEXT
)
""")
conn.commit()

print("MARIS Real Data Fetch Running...")

def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    res = requests.get(url, timeout=10)
    data = res.json()

    wind = data["current_weather"]["windspeed"]
    pressure = data["current_weather"].get("pressure", 1010)

    return wind, pressure


def get_wave():
    # NOAA WaveWatch sample (global grid)
    url = "https://nomads.ncep.noaa.gov/dods/wave/nww3/nww3_latest"
    
    # NOTE:
    # NOAA API tidak simple JSON → butuh parsing NetCDF normally
    # Untuk simple use, kita fallback ke estimation realistic:
    
    return None


def estimate_wave(wind):
    # fallback realistic formula (lebih masuk akal dari sebelumnya)
    return round(0.016 * (wind ** 1.5), 2)


# ===== LOOP =====
while True:
    try:
        for loc in LOCATIONS:
            wind, pressure = get_weather(loc["lat"], loc["lon"])

            wave = get_wave()

            if wave is None:
                wave = estimate_wave(wind)

            now = datetime.datetime.now().isoformat()

            cursor.execute("""
            INSERT INTO pressure_data (location, pressure, wind_speed, wave_height, created_at)
            VALUES (?, ?, ?, ?, ?)
            """, (loc["name"], pressure, wind, wave, now))

            conn.commit()

            print(f"{loc['name']} | Wind:{wind} kt | Wave:{wave} m | Pressure:{pressure}")

    except Exception as e:
        print("ERROR:", e)

    time.sleep(30)