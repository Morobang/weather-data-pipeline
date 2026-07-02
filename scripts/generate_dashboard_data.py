import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ============================================================
# CONFIG
# ============================================================
TIMEZONE      = "Africa/Johannesburg"
OUTPUT_DIR    = Path("docs/data")

MUNICIPALITIES = [
    {"name": "Buffalo City",            "province": "Eastern Cape", "type": "Metropolitan", "lat": -32.9833, "lon": 27.8667},
    {"name": "Nelson Mandela Bay",      "province": "Eastern Cape", "type": "Metropolitan", "lat": -33.9581, "lon": 25.6000},
    {"name": "Mangaung",                "province": "Free State",   "type": "Metropolitan", "lat": -29.0852, "lon": 26.1596},
    {"name": "City of Ekurhuleni",      "province": "Gauteng",      "type": "Metropolitan", "lat": -26.3592, "lon": 28.1456},
    {"name": "City of Johannesburg",    "province": "Gauteng",      "type": "Metropolitan", "lat": -26.2041, "lon": 28.0473},
    {"name": "City of Tshwane",         "province": "Gauteng",      "type": "Metropolitan", "lat": -25.7479, "lon": 28.2293},
    {"name": "eThekwini",               "province": "KwaZulu-Natal","type": "Metropolitan", "lat": -29.8587, "lon": 31.0218},
    {"name": "City of Cape Town",       "province": "Western Cape", "type": "Metropolitan", "lat": -33.9249, "lon": 18.4241},
    {"name": "Polokwane",               "province": "Limpopo",      "type": "Local",        "lat": -23.9045, "lon": 29.4689},
    {"name": "City of Mbombela",        "province": "Mpumalanga",   "type": "Local",        "lat": -25.4653, "lon": 30.9856},
    {"name": "Rustenburg",              "province": "North West",   "type": "Local",        "lat": -25.6672, "lon": 27.2423},
    {"name": "Sol Plaatje",             "province": "Northern Cape","type": "Local",        "lat": -28.7282, "lon": 24.7499},
    {"name": "Mahikeng",                "province": "North West",   "type": "Local",        "lat": -25.8503, "lon": 25.6442},
    {"name": "Emfuleni",                "province": "Gauteng",      "type": "Local",        "lat": -26.7000, "lon": 27.8000},
    {"name": "Msunduzi",                "province": "KwaZulu-Natal","type": "Local",        "lat": -29.6006, "lon": 30.3794},
    {"name": "Newcastle",               "province": "KwaZulu-Natal","type": "Local",        "lat": -27.7559, "lon": 29.9318},
    {"name": "George",                  "province": "Western Cape", "type": "Local",        "lat": -33.9646, "lon": 22.4617},
    {"name": "Stellenbosch",            "province": "Western Cape", "type": "Local",        "lat": -33.9321, "lon": 18.8602},
    {"name": "Bloemfontein",            "province": "Free State",   "type": "Local",        "lat": -29.0852, "lon": 26.1596},
    {"name": "Welkom",                  "province": "Free State",   "type": "Local",        "lat": -27.9833, "lon": 26.7333},
    {"name": "Lephalale",               "province": "Limpopo",      "type": "Local",        "lat": -23.6667, "lon": 27.7500},
    {"name": "Musina",                  "province": "Limpopo",      "type": "Local",        "lat": -22.3500, "lon": 30.0333},
    {"name": "Emalahleni",              "province": "Mpumalanga",   "type": "Local",        "lat": -25.8744, "lon": 29.2403},
    {"name": "Upington",                "province": "Northern Cape","type": "Local",        "lat": -28.4478, "lon": 21.2561},
    {"name": "Springbok",               "province": "Northern Cape","type": "Local",        "lat": -29.6639, "lon": 17.8864},
    {"name": "Kimberley",               "province": "Northern Cape","type": "Local",        "lat": -28.7282, "lon": 24.7499},
    {"name": "Klerksdorp",              "province": "North West",   "type": "Local",        "lat": -26.8676, "lon": 26.6517},
]

WEATHERCODE_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Heavy drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Heavy showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


# ============================================================
# FETCH WEATHER FOR ONE MUNICIPALITY
# ============================================================
def fetch_weather(municipality: dict, retries: int = 3) -> Optional[dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":   municipality["lat"],
        "longitude":  municipality["lon"],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "windspeed_10m_max",
            "weathercode",
            "sunrise",
            "sunset",
        ],
        "hourly": [
            "temperature_2m",
            "precipitation",
            "relativehumidity_2m",
            "uv_index",
        ],
        "timezone":      TIMEZONE,
        "forecast_days": 1,
    }
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  Attempt {attempt}/{retries} failed for {municipality['name']}: {e}")
            if attempt < retries:
                import time; time.sleep(2 ** attempt)
    return None


# ============================================================
# GENERATE latest_weather.json
# One record per municipality with today's weather
# ============================================================
def generate_latest_weather() -> list:
    print("Generating latest_weather.json...")
    records = []
    for m in MUNICIPALITIES:
        print(f"  Fetching {m['name']}...")
        data = fetch_weather(m)
        if not data:
            print(f"  SKIP {m['name']}")
            continue
        daily   = data["daily"]
        hourly  = data["hourly"]
        code    = daily["weathercode"][0]
        records.append({
            "municipality":   m["name"],
            "province":       m["province"],
            "type":           m["type"],
            "lat":            m["lat"],
            "lon":            m["lon"],
            "date":           daily["time"][0],
            "temp_max":       daily["temperature_2m_max"][0],
            "temp_min":       daily["temperature_2m_min"][0],
            "precipitation":  daily["precipitation_sum"][0],
            "windspeed_max":  daily["windspeed_10m_max"][0],
            "weathercode":    code,
            "weather_desc":   WEATHERCODE_DESCRIPTIONS.get(code, "Unknown"),
            "sunrise":        daily["sunrise"][0],
            "sunset":         daily["sunset"][0],
            "avg_temp":       round(sum(hourly["temperature_2m"]) / len(hourly["temperature_2m"]), 2),
            "avg_humidity":   round(sum(hourly["relativehumidity_2m"]) / len(hourly["relativehumidity_2m"]), 1),
            "max_uv":         max(hourly["uv_index"]),
            "is_rainy":       daily["precipitation_sum"][0] > 0,
        })
    return records


# ============================================================
# GENERATE province_summary.json
# Aggregated by province
# ============================================================
def generate_province_summary(records: list) -> list:
    print("Generating province_summary.json...")
    provinces = {}
    for r in records:
        p = r["province"]
        if p not in provinces:
            provinces[p] = {
                "province":        p,
                "date":            r["date"],
                "municipalities":  [],
                "temp_max_list":   [],
                "temp_min_list":   [],
                "avg_temp_list":   [],
                "precip_list":     [],
                "wind_list":       [],
                "rainy_count":     0,
            }
        provinces[p]["municipalities"].append(r["municipality"])
        provinces[p]["temp_max_list"].append(r["temp_max"])
        provinces[p]["temp_min_list"].append(r["temp_min"])
        provinces[p]["avg_temp_list"].append(r["avg_temp"])
        provinces[p]["precip_list"].append(r["precipitation"])
        provinces[p]["wind_list"].append(r["windspeed_max"])
        if r["is_rainy"]:
            provinces[p]["rainy_count"] += 1

    summary = []
    for p, d in provinces.items():
        summary.append({
            "province":             p,
            "date":                 d["date"],
            "municipality_count":   len(d["municipalities"]),
            "avg_temp_c":           round(sum(d["avg_temp_list"]) / len(d["avg_temp_list"]), 2),
            "max_temp_c":           max(d["temp_max_list"]),
            "min_temp_c":           min(d["temp_min_list"]),
            "total_precipitation":  round(sum(d["precip_list"]), 2),
            "avg_windspeed":        round(sum(d["wind_list"]) / len(d["wind_list"]), 1),
            "rainy_municipalities": d["rainy_count"],
        })

    return sorted(summary, key=lambda x: x["avg_temp_c"], reverse=True)


# ============================================================
# GENERATE pipeline_stats.json
# Pipeline metadata for the dashboard
# ============================================================
def generate_pipeline_stats(records: list) -> dict:
    print("Generating pipeline_stats.json...")
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "generated_at":         datetime.now().isoformat(),
        "date":                 today,
        "total_municipalities": 254,
        "total_provinces":      9,
        "municipalities_today": len(records),
        "days_of_history":      91,
        "silver_hourly_rows":   550560,
        "silver_daily_rows":    22940,
        "bronze_rows":          656,
        "dag_runs": [
            {"name": "backfill_weather", "status": "success", "ran_once": True,  "duration": "1h 39m"},
            {"name": "extract_weather",  "status": "success", "ran_once": False, "duration": "5h 31m"},
            {"name": "load_weather",     "status": "success", "ran_once": False, "duration": "16m"},
        ],
        "data_source": "Open-Meteo API (free, no key required)",
        "github_repo": "https://github.com/Morobang/weather-data-pipeline",
        "stack": ["Python", "Apache Airflow", "Docker", "PostgreSQL", "SODA", "pytest", "GitHub Actions"],
    }


# ============================================================
# MAIN
# ============================================================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = generate_latest_weather()
    province_summary = generate_province_summary(records)
    pipeline_stats   = generate_pipeline_stats(records)

    with open(OUTPUT_DIR / "latest_weather.json", "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved latest_weather.json — {len(records)} municipalities")

    with open(OUTPUT_DIR / "province_summary.json", "w") as f:
        json.dump(province_summary, f, indent=2)
    print(f"Saved province_summary.json — {len(province_summary)} provinces")

    with open(OUTPUT_DIR / "pipeline_stats.json", "w") as f:
        json.dump(pipeline_stats, f, indent=2)
    print("Saved pipeline_stats.json")

    print("\nDone. Files written to docs/data/")


if __name__ == "__main__":
    main()