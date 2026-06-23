import logging
from datawarehouse.data_utils import get_db_connection, load_sql

log = logging.getLogger(__name__)


# ============================================================
# WEATHERCODE DESCRIPTIONS
# Used to populate weather_description in silver.weather_daily
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
# VERIFY SILVER DATA
# Checks that silver tables have data after loading
# ============================================================
def verify_silver_loads(cursor) -> dict:
    """
    Checks row counts in silver tables.
    Returns a dict with counts for each table.
    """
    counts = {}

    cursor.execute("SELECT COUNT(*) FROM silver.weather_hourly")
    counts["weather_hourly"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM silver.weather_daily")
    counts["weather_daily"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM silver.dim_municipalities")
    counts["dim_municipalities"] = cursor.fetchone()[0]

    log.info("Silver row counts:")
    for table, count in counts.items():
        log.info(f"  silver.{table}: {count:,} rows")

    return counts


# ============================================================
# VERIFY GOLD VIEWS
# Checks that gold views return data after silver is loaded
# ============================================================
def verify_gold_views(cursor) -> dict:
    """
    Checks row counts in gold views.
    Returns a dict with counts for each view.
    """
    counts = {}

    views = [
        "daily_summary",
        "province_summary",
        "hottest_municipalities",
        "rainiest_municipalities",
        "weekly_trends",
        "city_comparison",
    ]

    for view in views:
        cursor.execute(f"SELECT COUNT(*) FROM gold.{view}")
        counts[view] = cursor.fetchone()[0]

    log.info("Gold view row counts:")
    for view, count in counts.items():
        log.info(f"  gold.{view}: {count:,} rows")

    return counts


# ============================================================
# VERIFY BRONZE DATA
# Checks that bronze tables have data after loading
# ============================================================
def verify_bronze_loads(cursor) -> dict:
    """
    Checks row counts in bronze tables.
    Returns a dict with counts for each table.
    """
    counts = {}

    cursor.execute("SELECT COUNT(*) FROM bronze.raw_weather_hourly")
    counts["raw_weather_hourly"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bronze.raw_weather_daily")
    counts["raw_weather_daily"] = cursor.fetchone()[0]

    log.info("Bronze row counts:")
    for table, count in counts.items():
        log.info(f"  bronze.{table}: {count:,} rows")

    return counts


# ============================================================
# RUN ALL VERIFICATIONS
# Called at the end of every DAG run
# ============================================================
def run_all_verifications() -> None:
    """
    Connects to the database and verifies all layers
    have data after a pipeline run.
    Logs a full summary of row counts across all tables.
    """
    conn   = get_db_connection()
    cursor = conn.cursor()

    log.info("=" * 60)
    log.info("PIPELINE VERIFICATION")
    log.info("=" * 60)

    try:
        bronze_counts = verify_bronze_loads(cursor)
        silver_counts = verify_silver_loads(cursor)
        gold_counts   = verify_gold_views(cursor)

        log.info("=" * 60)
        log.info("VERIFICATION SUMMARY")
        log.info("=" * 60)

        total_bronze = sum(bronze_counts.values())
        total_silver = sum(silver_counts.values())
        total_gold   = sum(gold_counts.values())

        log.info(f"Bronze total rows: {total_bronze:,}")
        log.info(f"Silver total rows: {total_silver:,}")
        log.info(f"Gold   total rows: {total_gold:,}")

        # flag any empty tables
        all_counts = {
            **{f"bronze.{k}": v for k, v in bronze_counts.items()},
            **{f"silver.{k}": v for k, v in silver_counts.items()},
            **{f"gold.{k}":   v for k, v in gold_counts.items()},
        }

        empty = [table for table, count in all_counts.items() if count == 0]
        if empty:
            log.warning(f"Empty tables/views detected: {', '.join(empty)}")
        else:
            log.info("All tables and views have data")

        log.info("=" * 60)

    except Exception as e:
        log.error(f"Verification failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET LATEST DATE IN SILVER
# Useful for knowing how fresh the data is
# ============================================================
def get_latest_weather_date() -> str:
    """
    Returns the most recent weather_date in silver.weather_daily.
    """
    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(weather_date)
        FROM silver.weather_daily
    """)
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    if result:
        log.info(f"Latest weather date in silver: {result}")
        return str(result)
    else:
        log.warning("No data found in silver.weather_daily")
        return None


# ============================================================
# GET PROVINCE SUMMARY FOR A DATE
# Quick check of what's in gold for a given date
# ============================================================
def get_province_summary(date: str) -> list:
    """
    Returns the province summary from gold for a given date.
    Useful for quick checks after a pipeline run.

    Args:
        date: YYYY-MM-DD format

    Returns:
        List of tuples with province summary data
    """
    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            province,
            total_municipalities,
            avg_temp_c,
            max_temp_c,
            min_temp_c,
            total_precipitation_mm
        FROM gold.province_summary
        WHERE weather_date = %s
        ORDER BY avg_temp_c DESC
    """, (date,))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if results:
        log.info(f"Province summary for {date}:")
        for row in results:
            log.info(
                f"  {row[0]:<20} "
                f"avg={row[2]}°C  "
                f"max={row[3]}°C  "
                f"rain={row[5]}mm"
            )
    else:
        log.warning(f"No province summary data found for {date}")

    return results