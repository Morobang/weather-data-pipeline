import pytest
import psycopg2
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "dags"))


# ============================================================
# DATABASE CONNECTION FIXTURE
# Connects to the real weather_db for integration tests
# ============================================================


@pytest.fixture
def db_connection():
    """
    Creates a real database connection for integration tests.
    Skips all tests if the database is not reachable.
    """
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            dbname="weather_db",
            user="rocket",
            password="rocket123",
            connect_timeout=5,
        )
        yield conn
        conn.close()
    except psycopg2.OperationalError as e:
        pytest.skip(f"Database not reachable — skipping integration tests: {e}")



@pytest.fixture
def cursor(db_connection):
    """Returns a database cursor."""
    cur = db_connection.cursor()
    yield cur
    cur.close()


# ============================================================
# SCHEMA TESTS
# ============================================================

def test_bronze_schema_exists(cursor):
    """Bronze schema must exist."""
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'bronze'
    """)
    assert cursor.fetchone() is not None


def test_silver_schema_exists(cursor):
    """Silver schema must exist."""
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'silver'
    """)
    assert cursor.fetchone() is not None


def test_gold_schema_exists(cursor):
    """Gold schema must exist."""
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name = 'gold'
    """)
    assert cursor.fetchone() is not None


# ============================================================
# TABLE EXISTENCE TESTS
# ============================================================

def test_bronze_hourly_table_exists(cursor):
    """bronze.raw_weather_hourly must exist."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'bronze'
        AND table_name = 'raw_weather_hourly'
    """)
    assert cursor.fetchone() is not None


def test_bronze_daily_table_exists(cursor):
    """bronze.raw_weather_daily must exist."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'bronze'
        AND table_name = 'raw_weather_daily'
    """)
    assert cursor.fetchone() is not None


def test_silver_hourly_table_exists(cursor):
    """silver.weather_hourly must exist."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'silver'
        AND table_name = 'weather_hourly'
    """)
    assert cursor.fetchone() is not None


def test_silver_daily_table_exists(cursor):
    """silver.weather_daily must exist."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'silver'
        AND table_name = 'weather_daily'
    """)
    assert cursor.fetchone() is not None


def test_dim_municipalities_table_exists(cursor):
    """silver.dim_municipalities must exist."""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'silver'
        AND table_name = 'dim_municipalities'
    """)
    assert cursor.fetchone() is not None


# ============================================================
# DATA EXISTENCE TESTS
# ============================================================

def test_bronze_hourly_has_data(cursor):
    """bronze.raw_weather_hourly must have rows."""
    cursor.execute("SELECT COUNT(*) FROM bronze.raw_weather_hourly")
    count = cursor.fetchone()[0]
    assert count > 0, "bronze.raw_weather_hourly is empty"


def test_bronze_daily_has_data(cursor):
    """bronze.raw_weather_daily must have rows."""
    cursor.execute("SELECT COUNT(*) FROM bronze.raw_weather_daily")
    count = cursor.fetchone()[0]
    assert count > 0, "bronze.raw_weather_daily is empty"


def test_silver_hourly_has_data(cursor):
    """silver.weather_hourly must have rows."""
    cursor.execute("SELECT COUNT(*) FROM silver.weather_hourly")
    count = cursor.fetchone()[0]
    assert count > 0, "silver.weather_hourly is empty"


def test_silver_daily_has_data(cursor):
    """silver.weather_daily must have rows."""
    cursor.execute("SELECT COUNT(*) FROM silver.weather_daily")
    count = cursor.fetchone()[0]
    assert count > 0, "silver.weather_daily is empty"


def test_dim_municipalities_has_all_entries(cursor):
    """silver.dim_municipalities must have 254 municipalities."""
    cursor.execute("SELECT COUNT(*) FROM silver.dim_municipalities")
    count = cursor.fetchone()[0]
    assert count == 254, f"Expected 254 municipalities, got {count}"


# ============================================================
# DATA QUALITY TESTS
# ============================================================

def test_silver_hourly_no_null_municipalities(cursor):
    """silver.weather_hourly must have no null municipality names."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM silver.weather_hourly
        WHERE municipality IS NULL
    """)
    count = cursor.fetchone()[0]
    assert count == 0, f"Found {count} null municipality names"


def test_silver_hourly_no_null_temperatures(cursor):
    """silver.weather_hourly must have no null temperatures."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM silver.weather_hourly
        WHERE temperature_c IS NULL
    """)
    count = cursor.fetchone()[0]
    assert count == 0, f"Found {count} null temperatures"


def test_silver_hourly_temperatures_in_sa_range(cursor):
    """All temperatures must be within SA range (-20 to 60)."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM silver.weather_hourly
        WHERE temperature_c < -20
        OR temperature_c > 60
    """)
    count = cursor.fetchone()[0]
    assert count == 0, f"Found {count} temperatures outside SA range"


def test_silver_hourly_no_negative_precipitation(cursor):
    """Precipitation must never be negative."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM silver.weather_hourly
        WHERE precipitation_mm < 0
    """)
    count = cursor.fetchone()[0]
    assert count == 0, f"Found {count} negative precipitation values"


def test_silver_daily_max_above_min(cursor):
    """Max temperature must always be above min temperature."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM silver.weather_daily
        WHERE temperature_max_c < temperature_min_c
    """)
    count = cursor.fetchone()[0]
    assert count == 0, f"Found {count} rows where max temp < min temp"


def test_all_9_provinces_in_silver(cursor):
    """All 9 provinces must be represented in silver."""
    cursor.execute("""
        SELECT COUNT(DISTINCT province)
        FROM silver.weather_hourly
    """)
    count = cursor.fetchone()[0]
    assert count == 9, f"Expected 9 provinces, got {count}"


# ============================================================
# GOLD VIEW TESTS
# ============================================================

def test_gold_daily_summary_has_data(cursor):
    """gold.daily_summary must return rows."""
    cursor.execute("SELECT COUNT(*) FROM gold.daily_summary")
    count = cursor.fetchone()[0]
    assert count > 0, "gold.daily_summary is empty"


def test_gold_province_summary_has_data(cursor):
    """gold.province_summary must return rows."""
    cursor.execute("SELECT COUNT(*) FROM gold.province_summary")
    count = cursor.fetchone()[0]
    assert count > 0, "gold.province_summary is empty"


def test_gold_hottest_municipalities_has_data(cursor):
    """gold.hottest_municipalities must return rows."""
    cursor.execute("SELECT COUNT(*) FROM gold.hottest_municipalities")
    count = cursor.fetchone()[0]
    assert count > 0, "gold.hottest_municipalities is empty"


def test_gold_daily_summary_rainy_hours_valid(cursor):
    """Rainy hours in gold must be between 0 and 24."""
    cursor.execute("""
        SELECT COUNT(*)
        FROM gold.daily_summary
        WHERE rainy_hours < 0
        OR rainy_hours > 24
    """)
    count = cursor.fetchone()[0]
    assert count == 0, f"Found {count} invalid rainy hour values"


def test_gold_province_summary_has_all_provinces(cursor):
    """Gold province summary must have all 9 provinces."""
    cursor.execute("""
        SELECT COUNT(DISTINCT province)
        FROM gold.province_summary
    """)
    count = cursor.fetchone()[0]
    assert count == 9, f"Expected 9 provinces in gold, got {count}"