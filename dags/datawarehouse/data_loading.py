import json
import logging
from pathlib import Path
from typing import Optional

from datawarehouse.data_utils import (
    get_db_connection,
    get_municipality_id,
    backfill_already_run,
)
from datawarehouse.data_modification import (
    insert_bronze_hourly,
    insert_bronze_daily,
    insert_silver_hourly,
    insert_silver_daily,
)

log = logging.getLogger(__name__)


# ============================================================
# LOAD A SINGLE JSON FILE INTO BRONZE + SILVER
# Used by both the daily DAG and the backfill DAG
# ============================================================
def load_json_file(filepath: str) -> None:
    """
    Reads a JSON file and loads all records into
    bronze and silver tables.

    Args:
        filepath: Path to the JSON file in /data/
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    log.info(f"Loading {path.name}")

    with open(path, "r") as f:
        records = json.load(f)

    log.info(f"Found {len(records)} municipality records in {path.name}")

    conn   = get_db_connection()
    cursor = conn.cursor()

    success = 0
    failed  = []

    for record in records:
        municipality = record["municipality"]
        province     = record["province"]

        try:
            # get municipality id from dim table
            municipality_id = get_municipality_id(cursor, municipality, province)

            # load into bronze
            insert_bronze_hourly(cursor, record)
            insert_bronze_daily(cursor, record)

            # load into silver
            insert_silver_hourly(cursor, record, municipality_id)
            insert_silver_daily(cursor, record, municipality_id)

            conn.commit()
            success += 1
            log.info(f"Loaded {municipality} successfully")

        except Exception as e:
            conn.rollback()
            log.error(f"Failed to load {municipality}: {e}")
            failed.append(municipality)

    cursor.close()
    conn.close()

    log.info("=" * 60)
    log.info(f"LOAD SUMMARY — {path.name}")
    log.info(f"Success: {success}")
    log.info(f"Failed:  {len(failed)}")
    if failed:
        log.warning(f"Failed municipalities: {', '.join(failed)}")
    log.info("=" * 60)


# ============================================================
# LOAD TODAY'S FORECAST FILE
# Called by the daily extract + load DAG
# ============================================================
def load_daily_forecast() -> None:
    """
    Loads today's forecast JSON file into bronze and silver.
    Called by the daily Airflow DAG after extraction.
    """
    from datetime import datetime
    today    = datetime.now().strftime("%Y-%m-%d")
    filepath = Path("data") / f"weather_municipalities_{today}.json"

    if not filepath.exists():
        raise FileNotFoundError(
            f"Today's forecast file not found: {filepath}. "
            f"Run the extraction DAG first."
        )

    log.info(f"Loading daily forecast for {today}")
    load_json_file(str(filepath))


# ============================================================
# LOAD HISTORICAL BACKFILL FILE
# Called once on first pipeline run
# ============================================================
def load_backfill() -> None:
    """
    Finds and loads the historical backfill JSON file.
    Skips if backfill has already been loaded.
    """
    conn   = get_db_connection()
    cursor = conn.cursor()

    # check if backfill already done
    if backfill_already_run(cursor):
        log.info("Backfill already loaded — skipping")
        cursor.close()
        conn.close()
        return

    cursor.close()
    conn.close()

    # find the backfill file
    data_dir = Path("data")
    backfill_files = list(data_dir.glob("weather_historical_*.json"))

    if not backfill_files:
        raise FileNotFoundError(
            "No historical backfill file found in /data/. "
            "Run weather_backfill.py first."
        )

    # use the most recent backfill file
    backfill_file = sorted(backfill_files)[-1]
    log.info(f"Loading backfill from {backfill_file.name}")
    load_json_file(str(backfill_file))