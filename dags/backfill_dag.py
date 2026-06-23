import sys
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/dags")
from api.weather_extract import backfill_historical
from datawarehouse.data_loading import load_backfill
from datawarehouse.data_transformation import run_all_verifications

log = logging.getLogger(__name__)

default_args = {
    "owner":            "rocket",
    "retries":          2,
    "retry_delay":      timedelta(minutes=10),
    "email_on_failure": False,
}

with DAG(
    dag_id="backfill_weather",
    description="One-time historical backfill — 90 days for all 257 municipalities",
    default_args=default_args,
    start_date=datetime(2026, 6, 1),
    schedule_interval="@once",
    catchup=False,
    tags=["weather", "backfill", "historical"],
) as dag:

    extract_historical_task = PythonOperator(
        task_id="extract_historical",
        python_callable=backfill_historical,
        op_kwargs={"days": 90},
    )

    load_historical_task = PythonOperator(
        task_id="load_historical",
        python_callable=load_backfill,
    )

    verify_task = PythonOperator(
        task_id="verify_all_layers",
        python_callable=run_all_verifications,
    )

    # extract first, then load, then verify
    extract_historical_task >> load_historical_task >> verify_task