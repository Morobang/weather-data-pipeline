import logging
from typing import Optional

log = logging.getLogger(__name__)

# ============================================================
# INSERT INTO BRONZE — RAW HOURLY
# One row per municipality per fetch
# Stores the entire hourly JSON blob untouched
# ============================================================
def insert_bronze_hourly(cursor, record: dict) -> None:
    """
    Inserts a raw hourly weather record into bronze.raw_weather_hourly.
    If the same municipality + date already exists, skip it.

    Args:
        cursor: Active database cursor
        record: Dictionary from the JSON file
    """
    import json

    data        = record["data"]
    elevation   = data.get("elevation")
    weather_date = data["hourly"]["time"][0][:10]  # first timestamp → date

    cursor.execute("""
        INSERT INTO bronze.raw_weather_hourly (
            municipality,
            province,
            municipality_type,
            lat,
            lon,
            elevation_m,
            fetched_at,
            weather_date,
            raw_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        record["municipality"],
        record["province"],
        record["type"],
        record["lat"],
        record["lon"],
        elevation,
        record["fetched_at"],
        weather_date,
        json.dumps(data["hourly"]),
    ))
    log.info(f"Bronze hourly inserted — {record['municipality']} {weather_date}")


# ============================================================
# INSERT INTO BRONZE — RAW DAILY
# One row per municipality per fetch
# Stores the entire daily JSON blob untouched
# ============================================================
def insert_bronze_daily(cursor, record: dict) -> None:
    """
    Inserts a raw daily weather record into bronze.raw_weather_daily.
    If the same municipality + date already exists, skip it.

    Args:
        cursor: Active database cursor
        record: Dictionary from the JSON file
    """
    import json

    data         = record["data"]
    elevation    = data.get("elevation")
    weather_date = data["daily"]["time"][0]  # first date

    cursor.execute("""
        INSERT INTO bronze.raw_weather_daily (
            municipality,
            province,
            municipality_type,
            lat,
            lon,
            elevation_m,
            fetched_at,
            weather_date,
            raw_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, (
        record["municipality"],
        record["province"],
        record["type"],
        record["lat"],
        record["lon"],
        elevation,
        record["fetched_at"],
        weather_date,
        json.dumps(data["daily"]),
    ))
    log.info(f"Bronze daily inserted — {record['municipality']} {weather_date}")


# ============================================================
# INSERT INTO SILVER — WEATHER HOURLY
# Explodes the hourly JSON into one row per hour
# 24 rows per municipality per day
# ============================================================
def insert_silver_hourly(cursor, record: dict, municipality_id: int) -> None:
    """
    Explodes hourly JSON and inserts one row per hour into
    silver.weather_hourly.

    Args:
        cursor:          Active database cursor
        record:          Dictionary from the JSON file
        municipality_id: FK from silver.dim_municipalities
    """
    data    = record["data"]
    hourly  = data["hourly"]
    daily   = data["daily"]

    # get sunrise and sunset for daytime calculation
    sunrise = daily.get("sunrise", [None])[0]
    sunset  = daily.get("sunset",  [None])[0]

    times        = hourly["time"]
    temperatures = hourly["temperature_2m"]
    precip       = hourly["precipitation"]
    windspeed    = hourly["windspeed_10m"]
    humidity     = hourly["relativehumidity_2m"]
    cloudcover   = hourly["cloudcover"]
    visibility   = hourly["visibility"]
    uv_index     = hourly["uv_index"]
    pressure     = hourly["surface_pressure"]

    rows_inserted = 0

    for i, timestamp in enumerate(times):
        # determine if this hour is daytime
        is_daytime = None
        if sunrise and sunset:
            is_daytime = sunrise <= timestamp <= sunset

        cursor.execute("""
            INSERT INTO silver.weather_hourly (
                municipality_id,
                municipality,
                province,
                municipality_type,
                recorded_at,
                weather_date,
                temperature_c,
                precipitation_mm,
                windspeed_kmh,
                humidity_pct,
                cloudcover_pct,
                visibility_m,
                uv_index,
                surface_pressure_hpa,
                is_daytime,
                loaded_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (municipality_id, recorded_at) DO NOTHING
        """, (
            municipality_id,
            record["municipality"],
            record["province"],
            record["type"],
            timestamp,
            timestamp[:10],
            temperatures[i],
            precip[i],
            windspeed[i],
            humidity[i],
            cloudcover[i],
            visibility[i],
            uv_index[i],
            pressure[i],
            is_daytime,
        ))
        rows_inserted += 1

    log.info(f"Silver hourly inserted — {record['municipality']} — {rows_inserted} rows")


# ============================================================
# WEATHERCODE DESCRIPTIONS
# WMO weather codes mapped to human readable descriptions
# ============================================================
WEATHERCODE_DESCRIPTIONS = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight showers",
    81: "Moderate showers",
    82: "Heavy showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


# ============================================================
# INSERT INTO SILVER — WEATHER DAILY
# One row per municipality per day
# ============================================================
def insert_silver_daily(cursor, record: dict, municipality_id: int) -> None:
    """
    Inserts one daily summary row per day into silver.weather_daily.

    Args:
        cursor:          Active database cursor
        record:          Dictionary from the JSON file
        municipality_id: FK from silver.dim_municipalities
    """
    data  = record["data"]
    daily = data["daily"]

    dates            = daily["time"]
    temp_max         = daily["temperature_2m_max"]
    temp_min         = daily["temperature_2m_min"]
    precip_sum       = daily["precipitation_sum"]
    windspeed_max    = daily["windspeed_10m_max"]
    sunrise          = daily["sunrise"]
    sunset           = daily["sunset"]
    daylight         = daily["daylight_duration"]
    weathercode      = daily["weathercode"]
    elevation        = data.get("elevation")

    rows_inserted = 0

    for i, date in enumerate(dates):
        code        = weathercode[i]
        description = WEATHERCODE_DESCRIPTIONS.get(code, "Unknown")

        cursor.execute("""
            INSERT INTO silver.weather_daily (
                municipality_id,
                municipality,
                province,
                municipality_type,
                weather_date,
                elevation_m,
                temperature_max_c,
                temperature_min_c,
                precipitation_sum_mm,
                windspeed_max_kmh,
                sunrise_at,
                sunset_at,
                daylight_duration_s,
                weathercode,
                weather_description,
                loaded_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (municipality_id, weather_date) DO NOTHING
        """, (
            municipality_id,
            record["municipality"],
            record["province"],
            record["type"],
            date,
            elevation,
            temp_max[i],
            temp_min[i],
            precip_sum[i],
            windspeed_max[i],
            sunrise[i],
            sunset[i],
            daylight[i],
            code,
            description,
        ))
        rows_inserted += 1

    log.info(f"Silver daily inserted — {record['municipality']} — {rows_inserted} rows")