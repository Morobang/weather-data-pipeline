import logging
from pathlib import Path
from soda.scan import Scan

log = logging.getLogger(__name__)


# ============================================================
# RUN SODA CHECKS
# Loads a YAML check file and runs it against the database
# Raises an exception if any check fails — halts the DAG
# ============================================================
def run_soda_checks(checks_file: str, data_source: str = "weather_db") -> None:
    """
    Runs SODA checks from a YAML file against the database.
    Raises an exception if any check fails.

    Args:
        checks_file: Path to the YAML checks file
        data_source: Name of the data source in SODA config
    """
    import os
    checks_path = Path(checks_file)
    if not checks_path.exists():
        raise FileNotFoundError(f"SODA checks file not found: {checks_file}")

    log.info(f"Running SODA checks from {checks_file}")

    scan = Scan()
    scan.set_scan_definition_name(checks_path.stem)
    scan.set_data_source_name(data_source)

    # add database connection
    scan.add_configuration_yaml_str(f"""
        data_sources:
          {data_source}:
            type: postgres
            host: {os.getenv('POSTGRES_HOST', 'postgres')}
            port: {os.getenv('POSTGRES_PORT', '5432')}
            database: {os.getenv('POSTGRES_DB', 'weather_db')}
            username: {os.getenv('POSTGRES_USER')}
            password: {os.getenv('POSTGRES_PASSWORD')}
            schema: public
    """)

    # add checks
    scan.add_sodacl_yaml_file(str(checks_path))

    # run
    scan.execute()

    # log results
    log.info(scan.get_logs_text())

    # raise if any checks failed
    if scan.has_check_failures():
        failures = scan.get_check_diagnostics_dict()
        log.error(f"SODA checks failed: {failures}")
        raise ValueError(f"SODA quality checks failed for {checks_file}")

    log.info(f"All SODA checks passed for {checks_file}")


# ============================================================
# INDIVIDUAL CHECK RUNNERS
# Called by Airflow tasks
# ============================================================
def run_bronze_checks() -> None:
    run_soda_checks("/opt/airflow/include/soda/bronze_checks.yml")


def run_silver_checks() -> None:
    run_soda_checks("/opt/airflow/include/soda/silver_checks.yml")


def run_gold_checks() -> None:
    run_soda_checks("/opt/airflow/include/soda/gold_checks.yml")