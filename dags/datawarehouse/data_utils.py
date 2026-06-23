import os
import logging
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

# ============================================================
# DATABASE CONNECTION
# Reads credentials from .env
# ============================================================
def get_db_connection():
    host     = os.getenv("POSTGRES_HOST", "localhost")  
    port     = os.getenv("POSTGRES_PORT", "5432")       
    dbname   = os.getenv("POSTGRES_DB",   "weather_db") 

    # ← no defaults for sensitive values
    # if these are missing the function raises immediately
    user     = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    if not user:
        raise ValueError("POSTGRES_USER not set in .env")
    if not password:
        raise ValueError("POSTGRES_PASSWORD not set in .env")

    log.info(f"Connecting to {dbname} on {host}:{port} as {user}")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        log.info("Database connection established")
        return conn
    except psycopg2.OperationalError as e:
        log.error(f"Failed to connect to database: {e}")
        raise



# ============================================================
# LOAD SQL FROM FILE
# This is the key function — no SQL strings in Python ever
# All SQL lives in scripts/ folder
# ============================================================
def load_sql(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {filepath}")
    sql = path.read_text()
    log.info(f"Loaded SQL from {filepath}")
    return sql


# ============================================================
# GET MUNICIPALITY ID
# Looks up the id from dim_municipalities
# Used when inserting into silver tables
# ============================================================
def get_municipality_id(cursor, municipality: str, province: str) -> int:
    cursor.execute("""
        SELECT id FROM silver.dim_municipalities
        WHERE municipality = %s AND province = %s
    """, (municipality, province))
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"Municipality not found in dim_municipalities: {municipality}, {province}")
    return result[0]


# ============================================================
# CHECK IF BACKFILL HAS BEEN RUN
# Prevents running the backfill more than once
# ============================================================
def backfill_already_run(cursor) -> bool:
    cursor.execute("SELECT COUNT(*) FROM bronze.raw_weather_daily")
    count = cursor.fetchone()[0]
    return count > 257